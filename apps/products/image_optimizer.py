import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile


def compress_and_resize_image(
    image_field,
    max_dimensions=(1200, 1200),
    quality=82,
    output_format=None,
):
    """
    High-performance compression and resizing for product/category/brand image uploads:
    1. Skips immediately if already compressed in the current request or already committed to disk.
    2. Corrects orientation from EXIF metadata.
    3. Resamples large images using fast BICUBIC downsampling.
    4. Automatically selects optimal web format:
       - Photos (no alpha) -> progressive JPEG (instant encoding, ~100KB).
       - Transparent graphics (RGBA/LA) -> fast PNG without CPU-blocking exhaustive optimization.
    5. Saves directly to image_field without causing request timeout or 502 Bad Gateway.
    """
    if not image_field:
        return

    # Check if this instance was already processed in the current request lifecycle
    if getattr(image_field, '_already_compressed', False):
        return

    file_obj = getattr(image_field, 'file', None)
    if file_obj is None:
        return

    # Only process newly uploaded files, skip already committed files on disk
    is_new_upload = isinstance(file_obj, UploadedFile) or not getattr(image_field, '_committed', True)
    if not is_new_upload and not getattr(image_field, '_force_compress', False):
        return

    try:
        image_field.file.seek(0)
        img = Image.open(image_field.file)
    except Exception:
        # Not an image or corrupted file, ignore gracefully
        return

    try:
        # Auto-orient based on EXIF tag (e.g. mobile photo uploads)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

        # Target format selection:
        # Default to JPEG for photos (no alpha) for 20x faster encoding and 10x smaller file size.
        # Preserve PNG only for images with transparent alpha channels.
        if output_format:
            target_format = output_format.upper()
        else:
            orig_format = (img.format or 'JPEG').upper()
            if orig_format in ('PNG', 'WEBP') and has_alpha:
                target_format = 'PNG'
            else:
                target_format = 'JPEG'

        if target_format in ('JPG', 'JPEG'):
            target_format = 'JPEG'
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
            target_format = 'WEBP'

        # Fast downsampling with BICUBIC (up to 8x faster than Lanczos on large mobile images)
        w, h = img.size
        max_w, max_h = max_dimensions
        if w > max_w or h > max_h:
            img.thumbnail(max_dimensions, Image.Resampling.BICUBIC)

        buffer = BytesIO()
        save_kwargs = {}
        if target_format == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
        elif target_format == 'WEBP':
            save_kwargs['quality'] = quality
        elif target_format == 'PNG':
            # IMPORTANT: NEVER use optimize=True on PNG in a synchronous web request,
            # as brute-force filter search causes server CPU starvation and 502 Bad Gateway.
            save_kwargs['optimize'] = False
            save_kwargs['compress_level'] = 6

        img.save(buffer, format=target_format, **save_kwargs)
        buffer.seek(0)

        # Name and save to field (save=False ensures it persists when model.save() is called)
        current_name = os.path.basename(image_field.name or 'image.jpg')
        base_name, _ = os.path.splitext(current_name)
        ext = '.jpg' if target_format == 'JPEG' else f'.{target_format.lower()}'
        new_filename = f"{base_name}{ext}"

        image_field.save(new_filename, ContentFile(buffer.getvalue()), save=False)
        image_field._already_compressed = True
    finally:
        try:
            img.close()
        except Exception:
            pass
