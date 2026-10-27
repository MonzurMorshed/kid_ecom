from django.shortcuts import render
from django.core.cache import cache
from products.models import Category, Product
from custom_admin.models import HeroSlide, Banner, SiteSettings


class HomeView:

    @staticmethod
    def index(request):
        # 1. Top-level categories (cached)
        categories = cache.get("nav_categories_cache")
        if categories is None:
            categories = list(
                Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")
            )
            cache.set("nav_categories_cache", categories, 3600)

        # 2. Dynamic Hero Slides query (cached)
        hero_slides = cache.get("home_hero_slides")
        if hero_slides is None:
            hero_slides = list(
                HeroSlide.objects.filter(is_active=True).order_by("sort_order", "created_at")
            )
            cache.set("home_hero_slides", hero_slides, 600)

        # 3. Dynamic Promotional Banners query (1 bulk query + cached)
        banners = cache.get("home_banners_dict")
        if banners is None:
            banners_qs = Banner.objects.filter(
                is_active=True,
                position__in=["home_top", "home_mid", "home_bottom"]
            ).order_by("sort_order", "id")
            banners = {}
            for b in banners_qs:
                if b.position not in banners:
                    banners[b.position] = b
            cache.set("home_banners_dict", banners, 600)

        home_top_banner = banners.get("home_top")
        home_mid_banner = banners.get("home_mid")
        home_bottom_banner = banners.get("home_bottom")

        # 4. Product sections (featured, bestsellers, recent) — cached together (5 min)
        home_products = cache.get("home_product_sections")
        if home_products is None:
            featured_products = list(
                Product.objects.filter(is_active=True, is_deleted=False, is_featured=True)
                .select_related("category")
                .prefetch_related("images")
                [:12]
            )
            bestsellers = list(
                Product.objects.filter(is_active=True, is_deleted=False, is_bestseller=True)
                .select_related("category")
                .prefetch_related("images")
                [:12]
            )
            recent_products = list(
                Product.objects.filter(is_active=True, is_deleted=False)
                .select_related("category")
                .prefetch_related("images")
                .order_by("-created_at")
                [:12]
            )
            home_products = {
                "featured": featured_products,
                "bestsellers": bestsellers,
                "recent": recent_products,
            }
            cache.set("home_product_sections", home_products, 300)

        featured_products = home_products["featured"]
        bestsellers = home_products["bestsellers"]
        recent_products = home_products["recent"]

        # 5. Announcement bar — uses cached SiteSettings singleton (0 DB queries)
        try:
            site_settings_obj = SiteSettings.get_settings()
            announcement = getattr(site_settings_obj, 'announcement_text', None) or \
                           "Free delivery on orders over ৳1,000 · Designed for curious little humans"
        except Exception:
            announcement = "Free delivery on orders over ৳1,000 · Designed for curious little humans"

        context = {
            "categories": categories,
            "featured_products": featured_products,
            "bestsellers": bestsellers,
            "recent_products": recent_products,
            "hero_slides": hero_slides,
            "home_top_banner": home_top_banner,
            "home_mid_banner": home_mid_banner,
            "home_bottom_banner": home_bottom_banner,
            "announcement": announcement,
        }
        return render(request, "storefront/index.html", context)