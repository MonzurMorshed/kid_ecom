"""
Context processors for the storefront app.
These inject data into every template automatically.
"""
from django.core.cache import cache
from products.models import Category
from .cart import Cart


def nav_categories(request):
    """Inject top-level active categories into every template for the navigation bar."""
    cats = cache.get("nav_categories_cache")
    if cats is None:
        try:
            cats = list(
                Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order")
            )
            cache.set("nav_categories_cache", cats, 3600)
        except Exception:
            cats = []
    return {
        "nav_categories": cats,
    }


def cart_context(request):
    """Inject cart item count, total, delivery fee, and grand total into every template."""
    if not hasattr(request, 'session'):
        return {
            "cart":              None,
            "cart_count":        0,
            "cart_total":        0,
            "cart_delivery_fee": 0,
            "cart_grand_total":  0,
        }
    if not hasattr(request, '_cart_instance'):
        request._cart_instance = Cart(request)
    cart = request._cart_instance
    return {
        "cart":              cart,
        "cart_count":        cart.item_count,
        "cart_total":        cart.total,
        "cart_delivery_fee": cart.delivery_fee,
        "cart_grand_total":  cart.grand_total,
    }


def site_settings(request):
    """
    Inject the SiteSettings singleton into every template context.
    Exposes:  site_settings.site_name, site_settings.site_tagline,
              site_settings.site_logo, site_settings.site_favicon,
              site_settings.site_email, site_settings.site_phone,
              site_settings.site_address,
              site_settings.currency, site_settings.currency_symbol,
              site_settings.free_shipping_threshold,
              site_settings.default_shipping_charge,
              site_settings.tax_rate,
              site_settings.facebook_url, site_settings.instagram_url,
              site_settings.twitter_url, site_settings.youtube_url,
              site_settings.maintenance_mode, site_settings.maintenance_msg
    """
    from custom_admin.models import SiteSettings  # local import avoids circular deps
    try:
        settings_obj = SiteSettings.get_settings()
    except Exception:
        settings_obj = None
    return {"site_settings": settings_obj}


def footer_pages(request):
    """
    Inject published pages configured to show in footer into every template.
    """
    pages = cache.get("footer_pages_cache")
    if pages is None:
        from custom_admin.models import Page
        try:
            pages = list(Page.objects.filter(is_published=True, show_in_footer=True).order_by('sort_order', 'title'))
            cache.set("footer_pages_cache", pages, 3600)
        except Exception:
            pages = []
    return {"footer_pages": pages}


def wishlist_context(request):
    """
    Inject wishlist_count and wishlist_ids for the current user into template context.
    Cached on request object so no duplicate queries occur during template rendering.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'wishlist_count': 0,
            'wishlist_ids': set(),
        }

    if not hasattr(request, '_wishlist_ids_cache'):
        from accounts.models import Wishlist
        try:
            ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
            request._wishlist_ids_cache = ids
            request._wishlist_count_cache = len(ids)
        except Exception:
            request._wishlist_ids_cache = set()
            request._wishlist_count_cache = 0

    return {
        'wishlist_count': request._wishlist_count_cache,
        'wishlist_ids': request._wishlist_ids_cache,
    }

