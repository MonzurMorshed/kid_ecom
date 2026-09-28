from django.shortcuts import render, get_object_or_404
from products.models import Category, Product


# How many products to show per product section
SECTION_LIMIT = 8

FILTER_PILLS = [
    {"key": "all",        "label": "All"},
    {"key": "bestseller", "label": "Best sellers"},
    {"key": "new",        "label": "New arrivals"},
    {"key": "featured",   "label": "Featured"},
    {"key": "under25",    "label": "Under ৳2,500"},
]


class ShopView:

    @staticmethod
    def shop(request):
        """General shop landing — redirects visually to the first active category."""
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")

        # Default: show the first category if one exists
        if categories.exists():
            selected = categories.first()
            return ShopView._render_category(request, selected, categories)

        context = {
            "categories": categories,
            "selected_category": None,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/shop.html", context)

    @staticmethod
    def category_detail(request, category_slug):
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")
        selected = get_object_or_404(Category, slug=category_slug, is_active=True)
        return ShopView._render_category(request, selected, categories)

    @staticmethod
    def _render_category(request, selected, categories):
        """Build the context for a selected category page."""
        base_qs = Product.objects.filter(
            category=selected,
            is_active=True,
            is_deleted=False,
        ).select_related("category").prefetch_related("images")

        # Filter pill from querystring (client-side Alpine mirrors this for instant UX)
        pill = request.GET.get("filter", "all")

        if pill == "bestseller":
            base_qs = base_qs.filter(is_bestseller=True)
        elif pill == "new":
            base_qs = base_qs.filter(is_new=True)
        elif pill == "featured":
            base_qs = base_qs.filter(is_featured=True)
        elif pill == "under25":
            base_qs = base_qs.filter(price__lt=2500)  # ৳2,500 ≈ ~$25
        # else: "all" – no extra filter

        most_loved = base_qs.filter(is_bestseller=True).order_by("-rating", "-created_at")[:SECTION_LIMIT]
        new_in = base_qs.filter(is_new=True).order_by("-created_at")[:SECTION_LIMIT]
        all_products = base_qs.order_by("-rating", "-created_at")[:SECTION_LIMIT]

        context = {
            "categories": categories,
            "selected_category": selected,
            "most_loved": most_loved,
            "new_in": new_in,
            "all_products": all_products,
            "active_pill": pill,
            "filter_pills": FILTER_PILLS,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/category_detail.html", context)
