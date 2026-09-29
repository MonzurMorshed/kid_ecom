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
    cart = Cart(request)
    return {
        "cart":              cart,
        "cart_count":        cart.item_count,
        "cart_total":        cart.total,
        "cart_delivery_fee": cart.delivery_fee,
        "cart_grand_total":  cart.grand_total,
    }
