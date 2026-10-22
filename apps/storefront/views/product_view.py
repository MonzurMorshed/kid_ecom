from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Category, Product, ProductReview
from custom_admin.models import SiteSettings


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

        # 1. Categories from cache (0 DB queries)
        categories = cache.get("nav_categories_cache")
        if categories is None:
            categories = list(Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order"))
            cache.set("nav_categories_cache", categories, 3600)

        # 2. Related products in the same category (with prefetch to avoid N+1 queries in cards)
        related = (
            Product.objects.filter(category=product.category, is_active=True, is_deleted=False)
            .exclude(pk=product.pk)
            .select_related("category")
            .prefetch_related("images")
            .order_by("-rating", "-created_at")[:4]
        )

        # 3. Customer reviews & rating breakdown (1 query total instead of 8 queries)
        reviews = list(product.reviews.filter(is_approved=True).select_related("user").order_by("-created_at"))
        reviews_count = len(reviews)
        rating_breakdown = product.get_rating_breakdown(approved_reviews=reviews)

        # 4. Wishlist state — server-side flag for authenticated customers
        is_wishlisted = False
        if request.user.is_authenticated:
            from accounts.models import Wishlist
            is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()

        # 5. Announcement bar — uses cached SiteSettings singleton
        try:
            site_settings_obj = SiteSettings.get_settings()
            announcement = getattr(site_settings_obj, 'announcement_text', None) or \
                           "Free delivery on orders over ৳1,000 · Designed for curious little humans"
        except Exception:
            announcement = "Free delivery on orders over ৳1,000 · Designed for curious little humans"

        context = {
            "product": product,
            "categories": categories,
            "related_products": related,
            "selected_category": product.category,
            "reviews": reviews,
            "reviews_count": reviews_count,
            "rating_breakdown": rating_breakdown,
            "announcement": announcement,
            "is_wishlisted": is_wishlisted,
        }
        return render(request, "storefront/product_detail.html", context)

