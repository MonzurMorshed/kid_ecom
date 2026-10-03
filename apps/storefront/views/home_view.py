from django.shortcuts import render
from products.models import Category, Product
from custom_admin.models import HeroSlide, Banner, SiteSettings


class HomeView:

    @staticmethod
    def index(request):
        # Top-level categories only (no sub-categories)
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order", "created_at")

        # Dynamic Hero Slides query
        hero_slides = HeroSlide.objects.filter(is_active=True).order_by("sort_order", "created_at")

        # Dynamic Promotional Banners query
        home_top_banner = Banner.objects.filter(is_active=True, position="home_top").first()
        home_mid_banner = Banner.objects.filter(is_active=True, position="home_mid").first()
        home_bottom_banner = Banner.objects.filter(is_active=True, position="home_bottom").first()

        # Featured products on homepage
        featured_products = (
            Product.objects.filter(is_active=True, is_deleted=False, is_featured=True)
            .select_related("category")
            .prefetch_related("images")
            [:8]
        )

        # Bestsellers on homepage
        bestsellers = (
            Product.objects.filter(is_active=True, is_deleted=False, is_bestseller=True)
            .select_related("category")
            .prefetch_related("images")
            [:4]
        )

        # Announcement bar — use site_settings from context processor when available,
        # fall back to a static string if SiteSettings has no announcement_text field.
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
            "hero_slides": hero_slides,
            "home_top_banner": home_top_banner,
            "home_mid_banner": home_mid_banner,
            "home_bottom_banner": home_bottom_banner,
            "announcement": announcement,
        }
        return render(request, "storefront/index.html", context)