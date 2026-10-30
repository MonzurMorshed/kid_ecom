import json
from django.http import JsonResponse
from django.db.models import Q
from products.models import Product, Category, Brand


def search_suggestions(request):
    """
    Live search autocomplete API.
    Returns JSON with matching products, categories, and brands.
    Query param: ?q=<search term>
    """
    q = request.GET.get("q", "").strip()

    # Require at least 2 characters to search
    if len(q) < 2:
        return JsonResponse({"query": q, "products": [], "categories": [], "brands": []})

    MAX_PRODUCTS   = 6
    MAX_CATEGORIES = 3
    MAX_BRANDS     = 3

    # --- Products ---
    product_qs = (
        Product.objects
        .filter(is_active=True, is_deleted=False)
        .filter(
            Q(title__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(category__name__icontains=q)
        )
        .select_related("brand", "category")
        .prefetch_related("images")
        .distinct()
        .order_by("-is_featured", "-is_bestseller", "-created_at")[:MAX_PRODUCTS]
    )

    products = []
    for p in product_qs:
        thumbnail = None
        primary = p.primary_image
        if primary and primary.image:
            try:
                thumbnail = primary.image.url
            except Exception:
                thumbnail = None

        products.append({
            "id": p.pk,
            "title": p.title,
            "slug": p.slug,
            "price": str(p.price),
            "compare_price": str(p.compare_price) if p.compare_price else None,
            "url": p.get_absolute_url(),
            "thumbnail": thumbnail,
            "category": p.category.name if p.category else None,
            "brand": p.brand.name if p.brand else None,
        })

    # --- Categories ---
    category_qs = (
        Category.objects
        .filter(is_active=True, name__icontains=q)
        .order_by("display_order", "name")[:MAX_CATEGORIES]
    )
    categories = [
        {"name": c.name, "slug": c.slug, "url": c.get_absolute_url()}
        for c in category_qs
    ]

    # --- Brands ---
    brand_qs = (
        Brand.objects
        .filter(is_active=True, name__icontains=q)
        .order_by("name")[:MAX_BRANDS]
    )
    brands = [
        {"name": b.name, "slug": b.slug}
        for b in brand_qs
    ]

    return JsonResponse({
        "query": q,
        "products": products,
        "categories": categories,
        "brands": brands,
    })
