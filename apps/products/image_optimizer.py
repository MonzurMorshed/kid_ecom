import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def compress_and_resize_image(
    image_field,
    max_dimensions=(1200, 1200),
    quality=82,
    output_format=None,
):
    """
    Compress and resize an image field upon upload:
    1. Skips if already compressed or no file buffer.
    2. Corrects orientation from EXIF metadata.
    3. Smoothly downsamples images exceeding max_dimensions with Lanczos resampling.
    4. Handles color profile & alpha channel (converting transparent RGBA to white background for JPEG).
    5. Optimizes and compresses file size using Pillow.
    6. Replaces the in-memory uploaded file content before disk write.
    """
    if not image_field:
        return

    # Check if this instance was already processed in the current request lifecycle
    if getattr(image_field, '_already_compressed', False):
        return

    # Must have an openable file
    if not hasattr(image_field, 'file') or image_field.file is None:
        return

    try:
        # Rewind and open
        image_field.file.seek(0)
        img = Image.open(image_field.file)
    except Exception:
        # Not an image or corrupted file, ignore gracefully
        return

    orig_format = img.format or 'JPEG'

    # Auto-orient based on EXIF tag (e.g. mobile photo uploads)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Target format selection
    target_format = output_format or orig_format
    if target_format.upper() in ('JPG', 'JPEG'):
        target_format = 'JPEG'
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            mask = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
            bg.paste(img, mask=mask)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
    elif target_format.upper() == 'WEBP':
        target_format = 'WEBP'
    elif target_format.upper() == 'PNG':
        target_format = 'PNG'

    # Resize/downsample if larger than bounds
    w, h = img.size
    max_w, max_h = max_dimensions
    if w > max_w or h > max_h:
        img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

    # Save to in-memory bytes
    buffer = BytesIO()
    save_kwargs = {'optimize': True}
    if target_format in ('JPEG', 'WEBP'):
        save_kwargs['quality'] = quality

    img.save(buffer, format=target_format, **save_kwargs)
    buffer.seek(0)

    # Name and save to field (save=False ensures it persists when model.save() is called)
    current_name = os.path.basename(image_field.name)
    base_name, _ = os.path.splitext(current_name)
    ext = '.jpg' if target_format == 'JPEG' else f'.{target_format.lower()}'
    new_filename = f"{base_name}{ext}"

    image_field.save(new_filename, ContentFile(buffer.getvalue()), save=False)
    image_field._already_compressed = True
