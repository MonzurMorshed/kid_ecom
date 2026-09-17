import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils.text import slugify

from apps.custom_admin.decorators import admin_required
from .models import Category, Product, Brand, ProductOption, ProductOptionValue, ProductVariant

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
    products = Product.objects.select_related('category', 'brand').prefetch_related('variants').all().order_by('-created_at')
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'custom_admin/products/product_list.html', context)

@admin_required
def product_create(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug')
        if not slug and title:
            slug = slugify(title, allow_unicode=True)

        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')

        product = Product.objects.create(
            title=title,
            slug=slug,
            category_id=category_id,
            price=price,
            stock=stock,
            description=description,
        )

        messages.success(request, "Product created successfully.")
        return redirect('custom_admin:product_list')

    context = {
        'categories': categories,
    }
    return render(request, 'custom_admin/products/product_list.html', context)

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