from django.shortcuts import render, get_object_or_404
from products.models import Category, Product


class ProductDetailView:

    @staticmethod
    def detail(request, slug):
        product = get_object_or_404(
            Product.objects.select_related("category", "brand").prefetch_related("images", "variants"),
            slug=slug,
            is_active=True,
            is_deleted=False,
        )
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")

        # Related products in the same category
        related = (
            Product.objects.filter(category=product.category, is_active=True, is_deleted=False)
            .exclude(pk=product.pk)
            .order_by("-rating", "-created_at")[:4]
        )

        context = {
            "product": product,
            "categories": categories,
            "related_products": related,
            "selected_category": product.category,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/product_detail.html", context)
