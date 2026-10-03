"""
Context processors for the storefront app.
These inject data into every template automatically.
"""
from products.models import Category
from .cart import Cart


def nav_categories(request):
    """Inject top-level active categories into every template for the navigation bar."""
    return {
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order"),
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
    cart = Cart(request)
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

