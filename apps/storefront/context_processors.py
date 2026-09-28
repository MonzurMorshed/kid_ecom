"""
Context processors for the storefront app.
These inject data into every template automatically.
"""
from products.models import Category


def nav_categories(request):
    """Inject top-level active categories into every template for the navigation bar."""
    return {
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order"),
    }
