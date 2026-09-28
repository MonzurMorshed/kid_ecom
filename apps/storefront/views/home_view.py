from django.shortcuts import render
from products.models import Category, Product


class HomeView:

    @staticmethod
    def index(request):
        # Top-level categories only (no sub-categories)
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order", "created_at")

        # Default: show featured products on homepage (no specific category selected)
        featured_products = (
            Product.objects.filter(is_active=True, is_deleted=False, is_featured=True)
            .select_related("category")
            .prefetch_related("images")
            [:8]
        )

        context = {
            "categories": categories,
            "featured_products": featured_products,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/index.html", context)