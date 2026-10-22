import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile


def _get_img_settings():
    """
    Load image optimization config from SiteSettings (with safe fallback).
    Returns a dict: {format, quality, max_w, max_h, thumb_w, thumb_h, hero_w, hero_h}
    """
    try:
        from custom_admin.models import SiteSettings
        s = SiteSettings.get_settings()
        return {
            'format':      getattr(s, 'img_format', 'WEBP') or 'WEBP',
            'quality':     int(getattr(s, 'img_quality', 82) or 82),
            'max_w':       int(getattr(s, 'img_max_width', 1200) or 1200),
            'max_h':       int(getattr(s, 'img_max_height', 1200) or 1200),
            'thumb_w':     int(getattr(s, 'img_thumb_width', 400) or 400),
            'thumb_h':     int(getattr(s, 'img_thumb_height', 400) or 400),
            'hero_w':      int(getattr(s, 'img_hero_width', 1600) or 1600),
            'hero_h':      int(getattr(s, 'img_hero_height', 900) or 900),
            'lazy_loading':bool(getattr(s, 'img_lazy_loading', True)),
        }
    except Exception:
        return {
            'format': 'WEBP', 'quality': 82,
            'max_w': 1200, 'max_h': 1200,
            'thumb_w': 400, 'thumb_h': 400,
            'hero_w': 1600, 'hero_h': 900,
            'lazy_loading': True,
        }


def compress_and_resize_image(
    image_field,
    max_dimensions=None,
    quality=None,
    output_format=None,
    use_thumb=False,
    use_hero=False,
):
    """
    High-performance compression and resizing for product/category/brand image uploads.

    Priority for settings:
      1. Explicit arguments passed by caller (e.g. max_dimensions=(500,500))
      2. SiteSettings (admin-configurable via Developer Settings)
      3. Built-in defaults (WEBP, 82, 1200x1200)

    Mode flags:
      use_thumb=True  → uses img_thumb_width / img_thumb_height from settings
      use_hero=True   → uses img_hero_width  / img_hero_height  from settings

    Steps:
      1. Skip already-compressed images in the same request.
      2. Skip committed (on-disk) files that were not force-marked.
      3. Auto-correct EXIF orientation.
      4. Downsample with fast BICUBIC if image exceeds max dimensions.
      5. Encode to target format (WebP recommended; JPEG/PNG fallback).
      6. Save back to image_field without triggering a DB save.
    """
    if not image_field:
        return

    if getattr(image_field, '_already_compressed', False):
        return

    file_obj = getattr(image_field, 'file', None)
    if file_obj is None:
        return

    is_new_upload = isinstance(file_obj, UploadedFile) or not getattr(image_field, '_committed', True)
    if not is_new_upload and not getattr(image_field, '_force_compress', False):
        return

    # ── Resolve settings ──────────────────────────────────────────────────────
    cfg = _get_img_settings()

    # Determine target dimensions
    if max_dimensions is not None:
        target_dims = max_dimensions
    elif use_hero:
        target_dims = (cfg['hero_w'], cfg['hero_h'])
    elif use_thumb:
        target_dims = (cfg['thumb_w'], cfg['thumb_h'])
    else:
        target_dims = (cfg['max_w'], cfg['max_h'])

    # Determine quality
    target_quality = quality if quality is not None else cfg['quality']
    target_quality = max(1, min(100, int(target_quality)))

    # Determine output format (explicit arg > SiteSettings > WEBP fallback)
    target_format = (output_format or cfg['format'] or 'WEBP').upper()
    if target_format == 'JPG':
        target_format = 'JPEG'

    # ── Open image ────────────────────────────────────────────────────────────
    try:
        image_field.file.seek(0)
        img = Image.open(image_field.file)
    except Exception:
        return

    try:
        # Auto-orient via EXIF (mobile photo uploads)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

        # ── Format selection ──────────────────────────────────────────────────
        if target_format == 'JPEG':
            if has_alpha:
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                mask = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                bg.paste(img, mask=mask)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')

        elif target_format == 'PNG':
            if img.mode not in ('RGB', 'RGBA', 'L', 'P'):
                img = img.convert('RGBA' if has_alpha else 'RGB')

        elif target_format == 'WEBP':
            # WebP supports both lossy (RGB) and lossless (RGBA)
            if has_alpha:
                if img.mode not in ('RGBA', 'LA'):
                    img = img.convert('RGBA')
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

        # ── Downsample ────────────────────────────────────────────────────────
        w, h = img.size
        max_w, max_h = target_dims
        if w > max_w or h > max_h:
            img.thumbnail(target_dims, Image.Resampling.BICUBIC)

        # ── Encode ────────────────────────────────────────────────────────────
        buffer = BytesIO()
        save_kwargs = {}

        if target_format == 'JPEG':
            save_kwargs['quality'] = target_quality
            save_kwargs['optimize'] = False          # single-pass: 5-10x faster on shared hosting
            save_kwargs['subsampling'] = 2
        elif target_format == 'WEBP':
            save_kwargs['quality'] = target_quality
            save_kwargs['method'] = 4                # balance: speed vs compression ratio
            if has_alpha:
                save_kwargs['lossless'] = False      # lossy RGBA still ~3x smaller than PNG
        elif target_format == 'PNG':
            save_kwargs['optimize'] = False          # NEVER True in a sync web request (CPU starvation)
            save_kwargs['compress_level'] = 6

        img.save(buffer, format=target_format, **save_kwargs)
        buffer.seek(0)

        # ── Save back to field ────────────────────────────────────────────────
        dir_name = os.path.dirname(image_field.name or '')
        current_name = os.path.basename(image_field.name or 'image.jpg')
        base_name, _ = os.path.splitext(current_name)
        ext_map = {'JPEG': '.jpg', 'WEBP': '.webp', 'PNG': '.png'}
        ext = ext_map.get(target_format, '.jpg')
        new_filename = f"{base_name}{ext}"
        if dir_name:
            target_save_name = os.path.join(dir_name, new_filename).replace('\\', '/')
        else:
            target_save_name = new_filename

        old_file_path = None
        if getattr(image_field, '_force_compress', False):
            try:
                if hasattr(image_field, 'path') and os.path.exists(image_field.path):
                    old_file_path = image_field.path
            except Exception:
                old_file_path = None

        image_field.save(target_save_name, ContentFile(buffer.getvalue()), save=False)
        image_field._already_compressed = True

        # Clean up old file on disk if filename/extension changed
        if old_file_path and hasattr(image_field, 'path'):
            try:
                new_path = image_field.path
                if os.path.abspath(old_file_path) != os.path.abspath(new_path) and os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except Exception:
                pass

    finally:
        try:
            img.close()
        except Exception:
            pass


def bulk_optimize_all_media():
    """
    Iterates through existing media images and re-optimizes them using current SiteSettings.
    Models covered:
      - HeroSlide (hero dimensions)
      - Banner (max dimensions)
      - ProductImage (max dimensions)
      - ProductVariant (max dimensions)
      - Category (thumb dimensions)
      - Brand (thumb dimensions)

    Returns a summary dict with statistics.
    """
    stats = {
        'total_found': 0,
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'saved_bytes': 0,
        'details': [],
    }

    from custom_admin.models import HeroSlide, Banner
    from products.models import ProductImage, ProductVariant, Category, Brand

    targets = [
        ('HeroSlide', HeroSlide, 'image', {'use_hero': True}),
        ('Banner', Banner, 'image', {}),
        ('ProductImage', ProductImage, 'image', {}),
        ('ProductVariant', ProductVariant, 'image', {}),
        ('Category', Category, 'image', {'use_thumb': True}),
        ('Brand', Brand, 'logo', {'use_thumb': True}),
    ]

    for model_name, model_cls, field_name, opt_kwargs in targets:
        try:
            qs = model_cls.objects.filter(**{f"{field_name}__isnull": False}).exclude(**{field_name: ''})
            for obj in qs.iterator():
                stats['total_found'] += 1
                img_field = getattr(obj, field_name, None)
                if not img_field or not img_field.name:
                    stats['skipped'] += 1
                    continue

                try:
                    # Check if file actually exists on storage
                    if not img_field.storage.exists(img_field.name):
                        stats['skipped'] += 1
                        continue

                    old_size = 0
                    try:
                        old_size = img_field.size
                    except Exception:
                        pass

                    # Force recompression
                    img_field._force_compress = True
                    img_field._already_compressed = False
                    compress_and_resize_image(img_field, **opt_kwargs)
                    obj.save(update_fields=[field_name])

                    new_size = 0
                    try:
                        new_size = img_field.size
                    except Exception:
                        pass

                    saved = max(0, old_size - new_size)
                    stats['saved_bytes'] += saved
                    stats['processed'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    stats['details'].append(f"{model_name} #{obj.pk}: {str(e)}")
        except Exception as e:
            stats['errors'] += 1
            stats['details'].append(f"{model_name} query error: {str(e)}")

    return stats

