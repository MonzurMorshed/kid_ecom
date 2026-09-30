from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Category, Product, ProductReview


class ProductDetailView:

    @staticmethod
    def detail(request, slug):
        product = get_object_or_404(
            Product.objects.select_related("category", "brand").prefetch_related("images", "variants"),
            slug=slug,
            is_active=True,
            is_deleted=False,
        )

        # Handle review submission
        if request.method == "POST" and ("submit_review" in request.POST or request.headers.get("x-requested-with") == "XMLHttpRequest"):
            try:
                rating = int(request.POST.get("rating", 5))
                rating = max(1, min(5, rating))
            except (ValueError, TypeError):
                rating = 5

            name = request.POST.get("name", "").strip()
            email = request.POST.get("email", "").strip()
            title = request.POST.get("title", "").strip()
            comment = request.POST.get("comment", "").strip()

            if request.user.is_authenticated:
                user = request.user
                if not name:
                    name = user.get_full_name() or user.username or "Parent"
                if not email:
                    email = user.email
            else:
                user = None
                if not name:
                    name = "Verified Parent"

            if comment:
                review = ProductReview.objects.create(
                    product=product,
                    user=user,
                    name=name,
                    email=email,
                    rating=rating,
                    title=title,
                    comment=comment,
                    is_approved=True,
                )
                success_msg = "Thank you! Your review has been published."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": True,
                        "message": success_msg,
                        "rating": product.rating,
                        "reviews_count": product.review_count,
                    })
                messages.success(request, success_msg)
            else:
                error_msg = "Please write a comment for your review."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg}, status=400)
                messages.error(request, error_msg)

            return redirect("storefront:product_detail", slug=product.slug)

        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")

        # Related products in the same category
        related = (
            Product.objects.filter(category=product.category, is_active=True, is_deleted=False)
            .exclude(pk=product.pk)
            .order_by("-rating", "-created_at")[:4]
        )

        # Customer reviews
        reviews = product.reviews.filter(is_approved=True).select_related("user").order_by("-created_at")
        reviews_count = reviews.count()
        rating_breakdown = product.get_rating_breakdown()

        context = {
            "product": product,
            "categories": categories,
            "related_products": related,
            "selected_category": product.category,
            "reviews": reviews,
            "reviews_count": reviews_count,
            "rating_breakdown": rating_breakdown,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/product_detail.html", context)
