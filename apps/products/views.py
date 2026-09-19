import csv
import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils.text import slugify

from apps.custom_admin.decorators import admin_required
from .models import Category, Product, Brand, ProductOption, ProductOptionValue, ProductVariant, ProductImage

# =========================================================
# CATEGORY VIEWS
# =========================================================

@admin_required
def category_list(request):
    categories = Category.objects.select_related('parent').all().order_by('-created_at')
    return render(request, 'custom_admin/categories/category_list.html', {'categories': categories})

@admin_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        if not slug and name:
            slug = slugify(name, allow_unicode=True)

        parent_id = request.POST.get('parent')
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
        image = request.FILES.get('image')

        parent = Category.objects.filter(id=parent_id).first() if parent_id else None

        Category.objects.create(
            name=name,
            slug=slug,
            parent=parent,
            image=image,
            is_active=is_active
        )
        messages.success(request, "Category created successfully.")
        return redirect('custom_admin:category_list')

    parent_categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'custom_admin/categories/category_form.html', {'parent_categories': parent_categories})

@admin_required
def category_update(request, pk):
    category = get_object_or_404(Category, id=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        if not slug and name:
            slug = slugify(name, allow_unicode=True)

        parent_id = request.POST.get('parent')
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
        image = request.FILES.get('image')

        parent = Category.objects.filter(id=parent_id).exclude(id=pk).first() if parent_id else None

        category.name = name
        category.slug = slug
        category.parent = parent
        category.is_active = is_active
        if image:
            category.image = image
        category.save()

        messages.success(request, "Category updated successfully.")
        return redirect('custom_admin:category_list')

    parent_categories = Category.objects.filter(parent__isnull=True).exclude(id=pk)
    return render(request, 'custom_admin/categories/category_form.html', {
        'parent_categories': parent_categories,
        'category': category
    })


# =========================================================
# PRODUCT VIEWS
# =========================================================

@admin_required
def product_list(request):
    qs = (
        Product.objects
        .select_related('category', 'brand')
        .prefetch_related('variants')
        .filter(is_deleted=False)
        .order_by('-created_at')
    )

    # ── Search & Filter ──
    q          = request.GET.get('q', '').strip()
    cat_id     = request.GET.get('category', '').strip()
    brand_id   = request.GET.get('brand', '').strip()
    status     = request.GET.get('status', '').strip()   # 'active' | 'inactive'

    if q:
        qs = qs.filter(title__icontains=q)
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if brand_id:
        qs = qs.filter(brand_id=brand_id)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator  = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj   = paginator.get_page(page_number)

    context = {
        'page_obj'   : page_obj,
        'categories' : Category.objects.filter(is_active=True).order_by('name'),
        'brands'     : Brand.objects.filter(is_active=True).order_by('name'),
        'q'          : q,
        'cat_id'     : cat_id,
        'brand_id'   : brand_id,
        'status'     : status,
        'total_count': qs.count(),
    }
    return render(request, 'custom_admin/products/product_list.html', context)

@admin_required
def product_create(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        if not slug and title:
            slug = slugify(title, allow_unicode=True)

        category_id = request.POST.get('category') or None
        brand_id = request.POST.get('brand') or None
        price = request.POST.get('price', '0')
        stock = request.POST.get('stock', '0')
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, 'Product title is required.')
            return render(request, 'custom_admin/products/product_create.html', {
                'categories': categories, 'brands': brands,
            })

        # Ensure slug uniqueness
        original_slug = slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        product = Product.objects.create(
            title=title,
            slug=slug,
            category_id=category_id,
            brand_id=brand_id,
            price=price,
            stock=stock,
            description=description,
            is_active=is_active,
        )

        # ── Options & Variants ──
        try:
            options_json = request.POST.get('options_json', '[]')
            variants_json = request.POST.get('variants_json', '[]')
            options_data = json.loads(options_json)   # [{name, values:[...]}, ...]
            variants_data = json.loads(variants_json) # [{sku, stock, price, option_indices:{optIdx: valIdx}},...]

            # Create options and collect value objects keyed by (optIdx, valIdx)
            value_map = {}  # (opt_index, val_index) -> ProductOptionValue
            for opt_idx, opt in enumerate(options_data):
                opt_name = opt.get('name', '').strip()
                if not opt_name:
                    continue
                option_obj, _ = ProductOption.objects.get_or_create(
                    product=product, name=opt_name
                )
                for val_idx, val in enumerate(opt.get('values', [])):
                    val = val.strip()
                    if val:
                        val_obj, _ = ProductOptionValue.objects.get_or_create(
                            option=option_obj, value=val
                        )
                        value_map[(opt_idx, val_idx)] = val_obj

            # Create variants
            for variant in variants_data:
                sku = variant.get('sku', '').strip()
                if not sku:
                    continue
                v_stock = int(variant.get('stock', 0))
                v_price = variant.get('price') or None
                v_obj = ProductVariant.objects.create(
                    product=product,
                    sku=sku,
                    stock=v_stock,
                    price_override=v_price if v_price else None,
                )
                # Assign option values
                for opt_idx_str, val_idx in variant.get('option_values', {}).items():
                    key = (int(opt_idx_str), int(val_idx))
                    if key in value_map:
                        v_obj.options.add(value_map[key])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass  # Don't fail the whole product creation

        featured_image = request.FILES.get('featured_image')
        if featured_image:
            ProductImage.objects.create(
                product=product,
                image=featured_image,
                is_feature=True,
            )

        # Save additional gallery images
        gallery_images = request.FILES.getlist('gallery_images')
        for img in gallery_images:
            ProductImage.objects.create(
                product=product,
                image=img,
                is_feature=False,
            )

        messages.success(request, f'"{product.title}" created successfully.')
        return redirect('custom_admin:product_detail', pk=product.pk)

    context = {
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'custom_admin/products/product_create.html', context)


@admin_required
def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    context = {
        'product': product,
    }
    return render(request, 'custom_admin/products/product_details.html', context)


@admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        if not slug and title:
            slug = slugify(title, allow_unicode=True)

        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand') or None
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Ensure slug uniqueness (exclude current product)
        if slug != product.slug and Product.objects.filter(slug=slug).exclude(pk=pk).exists():
            original_slug = slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

        product.title = title or product.title
        product.slug = slug
        product.category_id = category_id
        product.brand_id = brand_id
        product.price = price
        product.stock = stock
        product.description = description
        product.is_active = is_active
        product.save()

        # Handle featured image upload
        featured_image = request.FILES.get('featured_image')
        if featured_image:
            # Remove old featured image if exists
            ProductImage.objects.filter(product=product, is_feature=True).delete()
            ProductImage.objects.create(
                product=product,
                image=featured_image,
                is_feature=True,
            )

        # Handle additional gallery images
        gallery_images = request.FILES.getlist('gallery_images')
        for img in gallery_images:
            ProductImage.objects.create(
                product=product,
                image=img,
                is_feature=False,
            )

        messages.success(request, f'"{product.title}" updated successfully.')
        return redirect('custom_admin:product_detail', pk=product.pk)

    context = {
        'product': product,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'custom_admin/products/product_form.html', context)


@admin_required
def product_image_delete(request, image_pk):
    """Delete a single ProductImage."""
    img = get_object_or_404(ProductImage, pk=image_pk)
    product_pk = img.product_id
    if request.method == 'POST':
        img.delete()
        messages.success(request, 'Image removed successfully.')
    return redirect('custom_admin:product_detail', pk=product_pk)


# =========================================================
# VARIANT VIEWS
# =========================================================

@admin_required
def variant_add(request, pk):
    """Add a single variant to an existing product."""
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    if request.method == 'POST':
        sku = request.POST.get('sku', '').strip()
        stock = request.POST.get('stock', '0')
        price_override = request.POST.get('price_override', '').strip() or None
        is_active = request.POST.get('is_active') == 'on'
        value_ids = request.POST.getlist('option_values')  # list of ProductOptionValue PKs

        if not sku:
            messages.error(request, 'SKU is required for a variant.')
            return redirect('custom_admin:product_update', pk=pk)

        if ProductVariant.objects.filter(sku=sku).exists():
            messages.error(request, f'SKU "{sku}" already exists.')
            return redirect('custom_admin:product_update', pk=pk)

        variant = ProductVariant.objects.create(
            product=product,
            sku=sku,
            stock=int(stock),
            price_override=price_override,
            is_active=is_active,
        )
        if value_ids:
            values = ProductOptionValue.objects.filter(
                pk__in=value_ids, option__product=product
            )
            variant.options.set(values)

        messages.success(request, f'Variant "{sku}" added.')
    return redirect('custom_admin:product_update', pk=pk)


@admin_required
def variant_delete(request, variant_pk):
    """Delete a single variant."""
    variant = get_object_or_404(ProductVariant, pk=variant_pk)
    product_pk = variant.product_id
    if request.method == 'POST':
        sku = variant.sku
        variant.delete()
        messages.success(request, f'Variant "{sku}" deleted.')
    return redirect('custom_admin:product_update', pk=product_pk)



@admin_required
def product_soft_delete(request, pk):
    """Soft-delete a product (sets is_deleted=True, does not remove from DB)."""
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    if request.method == 'POST':
        product.soft_delete()
        messages.success(request, f'"{product.title}" has been moved to trash.')
    return redirect('custom_admin:product_list')


@admin_required
def product_trash(request):
    """Recycle bin – list of soft-deleted products."""
    deleted_products = (
        Product.objects
        .select_related('category', 'brand')
        .filter(is_deleted=True)
        .order_by('-deleted_at')
    )
    paginator   = Paginator(deleted_products, 15)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'custom_admin/products/product_trash.html', context)


@admin_required
def product_restore(request, pk):
    """Restore a soft-deleted product back to the active catalog."""
    product = get_object_or_404(Product, pk=pk, is_deleted=True)
    if request.method == 'POST':
        product.restore()
        messages.success(request, f'"{product.title}" has been restored.')
    return redirect('custom_admin:product_trash')


@admin_required
def product_permanent_delete(request, pk):
    """Permanently remove a soft-deleted product from the database."""
    product = get_object_or_404(Product, pk=pk, is_deleted=True)
    if request.method == 'POST':
        title = product.title
        product.delete()
        messages.success(request, f'"{title}" has been permanently deleted.')
    return redirect('custom_admin:product_trash')


# =========================================================
# PRODUCT OPTION VIEWS
# =========================================================

@admin_required
def option_add(request, pk):
    """Add a new option group (e.g. Size, Color) to a product."""
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            _, created = ProductOption.objects.get_or_create(product=product, name=name)
            if created:
                messages.success(request, f'Option "{name}" added.')
            else:
                messages.warning(request, f'Option "{name}" already exists.')
        else:
            messages.error(request, 'Option name cannot be empty.')
    return redirect('custom_admin:product_detail', pk=pk)


@admin_required
def option_delete(request, option_pk):
    """Delete an option group and all its values (cascades via FK)."""
    option = get_object_or_404(ProductOption, pk=option_pk)
    product_pk = option.product_id
    if request.method == 'POST':
        name = option.name
        option.delete()
        messages.success(request, f'Option "{name}" and all its values have been removed.')
    return redirect('custom_admin:product_detail', pk=product_pk)


@admin_required
def option_value_add(request, option_pk):
    """Add a new value (e.g. Small, Red) to an existing option group."""
    option = get_object_or_404(ProductOption, pk=option_pk)
    product_pk = option.product_id
    if request.method == 'POST':
        value = request.POST.get('value', '').strip()
        if value:
            _, created = ProductOptionValue.objects.get_or_create(option=option, value=value)
            if created:
                messages.success(request, f'Value "{value}" added to {option.name}.')
            else:
                messages.warning(request, f'"{value}" already exists in {option.name}.')
        else:
            messages.error(request, 'Value cannot be empty.')
    return redirect('custom_admin:product_detail', pk=product_pk)


@admin_required
def option_value_delete(request, value_pk):
    """Delete a single option value."""
    value = get_object_or_404(ProductOptionValue, pk=value_pk)
    product_pk = value.option.product_id
    if request.method == 'POST':
        label = f'{value.option.name}: {value.value}'
        value.delete()
        messages.success(request, f'Value "{label}" removed.')
    return redirect('custom_admin:product_detail', pk=product_pk)


@admin_required
def product_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'product_id', 'title', 'slug', 'category_id', 'category', 'brand', 
        'base_price', 'base_stock', 'sku', 'variant_options', 'variant_price', 
        'variant_stock', 'is_active', 'description'
    ])

    products = Product.objects.select_related('category', 'brand').prefetch_related('variants__options__option').all()

    for product in products:
        variants = product.variants.all()
        if variants.exists():
            for variant in variants:
                # Build option string e.g. "Size:Medium|Color:Red"
                option_str_parts = []
                for val in variant.options.all():
                    option_str_parts.append(f"{val.option.name}:{val.value}")
                variant_options = "|".join(option_str_parts)

                writer.writerow([
                    product.id,
                    product.title,
                    product.slug,
                    product.category_id or '',
                    product.category.name if product.category else '',
                    product.brand.name if product.brand else '',
                    product.price,
                    product.stock,
                    variant.sku,
                    variant_options,
                    variant.price_override if variant.price_override is not None else '',
                    variant.stock,
                    variant.is_active,
                    product.description or '',
                ])
        else:
            writer.writerow([
                product.id,
                product.title,
                product.slug,
                product.category_id or '',
                product.category.name if product.category else '',
                product.brand.name if product.brand else '',
                product.price,
                product.stock,
                '', # sku
                '', # variant_options
                '', # variant_price
                '', # variant_stock
                product.is_active,
                product.description or '',
            ])

    return response

@admin_required
def product_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_products_import.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'product_id', 'title', 'slug', 'category_id', 'category', 'brand', 
        'base_price', 'base_stock', 'sku', 'variant_options', 'variant_price', 
        'variant_stock', 'is_active', 'description'
    ])
    
    # Sample Simple Product
    writer.writerow([
        '', 'Wooden Building Blocks Set', 'wooden-building-blocks-set', '1', 'Toys', 'Kidurabd', 
        '1200.00', '15', '', '', '', '', 'True', 'Educational wooden toy set.'
    ])
    
    # Sample Variant Product - Base / Variant 1
    writer.writerow([
        '', 'Kids Cotton T-Shirt', 'kids-cotton-tshirt', '2', 'Clothing', 'Kidurabd', 
        '450.00', '50', 'TS-S-BLUE', 'Size:Small|Color:Blue', '450.00', '15', 'True', 'Comfortable cotton t-shirt.'
    ])
    
    # Sample Variant Product - Variant 2
    writer.writerow([
        '', 'Kids Cotton T-Shirt', 'kids-cotton-tshirt', '2', 'Clothing', 'Kidurabd', 
        '450.00', '50', 'TS-M-RED', 'Size:Medium|Color:Red', '480.00', '20', 'True', 'Comfortable cotton t-shirt.'
    ])

    return response

@admin_required
def product_import(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid .csv file.")
            return redirect('custom_admin:product_list')

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            created_count = 0
            updated_count = 0
            variant_count = 0

            current_product = None

            for row in reader:
                title = row.get('title', '').strip()
                slug = row.get('slug', '').strip()
                product_id = row.get('product_id', '').strip() or row.get('id', '').strip()

                # If row contains product info (title or product_id or slug)
                if title or product_id or slug:
                    if not title and current_product:
                        title = current_product.title
                    
                    if not slug and title:
                        slug = slugify(title, allow_unicode=True)

                    category_id_val = row.get('category_id', '').strip()
                    category_name = row.get('category', '').strip()
                    category = None

                    if category_id_val and category_id_val.isdigit():
                        category = Category.objects.filter(id=int(category_id_val)).first()

                    if not category and category_name:
                        category, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'slug': slugify(category_name, allow_unicode=True)}
                        )

                    if not category:
                        category, _ = Category.objects.get_or_create(
                            name='General',
                            defaults={'slug': 'general'}
                        )

                    brand_name = row.get('brand', '').strip()
                    brand = None
                    if brand_name:
                        brand, _ = Brand.objects.get_or_create(
                            name=brand_name,
                            defaults={'slug': slugify(brand_name, allow_unicode=True)}
                        )

                    base_price = row.get('base_price', '').strip() or row.get('price', '0.00').strip() or '0.00'
                    base_stock = row.get('base_stock', '').strip() or row.get('stock', '0').strip() or '0'
                    description = row.get('description', '').strip()
                    is_active_raw = str(row.get('is_active', 'True')).strip().lower()
                    is_active = is_active_raw in ['true', '1', 'yes', 'on']

                    # Check for existing product by ID or Slug
                    product = None
                    if product_id and product_id.isdigit():
                        product = Product.objects.filter(id=int(product_id)).first()
                    if not product and slug:
                        product = Product.objects.filter(slug=slug).first()

                    if product:
                        product.title = title or product.title
                        product.category = category or product.category
                        if brand:
                            product.brand = brand
                        product.price = base_price
                        product.stock = base_stock
                        if description:
                            product.description = description
                        product.is_active = is_active
                        product.save()
                        updated_count += 1
                        current_product = product
                    else:
                        # Ensure slug uniqueness
                        original_slug = slug
                        counter = 1
                        while Product.objects.filter(slug=slug).exists():
                            slug = f"{original_slug}-{counter}"
                            counter += 1

                        current_product = Product.objects.create(
                            title=title or 'Untitled Product',
                            slug=slug,
                            category=category,
                            brand=brand,
                            price=base_price,
                            stock=base_stock,
                            description=description,
                            is_active=is_active
                        )
                        created_count += 1

                # Now process Variant if SKU or variant_options is present
                sku = row.get('sku', '').strip()
                variant_options_str = row.get('variant_options', '').strip()
                variant_price = row.get('variant_price', '').strip()
                variant_stock = row.get('variant_stock', '0').strip() or '0'

                if current_product and (sku or variant_options_str):
                    option_values_to_link = []

                    if variant_options_str:
                        # Parse e.g. "Size:Medium|Color:Red"
                        option_pairs = variant_options_str.split('|')
                        for pair in option_pairs:
                            if ':' in pair:
                                opt_name, val_name = pair.split(':', 1)
                                opt_name = opt_name.strip()
                                val_name = val_name.strip()

                                if opt_name and val_name:
                                    option_obj, _ = ProductOption.objects.get_or_create(
                                        product=current_product,
                                        name=opt_name
                                    )
                                    val_obj, _ = ProductOptionValue.objects.get_or_create(
                                        option=option_obj,
                                        value=val_name
                                    )
                                    option_values_to_link.append(val_obj)

                    # Auto-generate SKU if empty
                    if not sku:
                        sku = f"{current_product.slug}-v{ProductVariant.objects.filter(product=current_product).count() + 1}"

                    variant = ProductVariant.objects.filter(sku=sku).first()
                    price_override_val = float(variant_price) if variant_price else None

                    if variant:
                        variant.price_override = price_override_val
                        variant.stock = int(variant_stock)
                        variant.save()
                    else:
                        variant = ProductVariant.objects.create(
                            product=current_product,
                            sku=sku,
                            price_override=price_override_val,
                            stock=int(variant_stock),
                            is_active=True
                        )

                    if option_values_to_link:
                        variant.options.set(option_values_to_link)

                    variant_count += 1

            messages.success(request, f"Import complete! {created_count} products created, {updated_count} updated, and {variant_count} variants processed.")
        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")

    return redirect('custom_admin:product_list')