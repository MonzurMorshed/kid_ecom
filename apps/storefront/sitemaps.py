from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Product, Category
from custom_admin.models import Page


class StaticViewSitemap(Sitemap):
    """Sitemap for key static storefront pages."""
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return ['storefront:index', 'storefront:shop', 'storefront:cart']

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    """Sitemap for all active product categories."""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Category.objects.filter(is_active=True).order_by('display_order', 'name')


class ProductSitemap(Sitemap):
    """Sitemap for all active, published products."""
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True, is_deleted=False).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    """Sitemap for published dynamic CMS pages (About, Terms, etc.)."""
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Page.objects.filter(is_published=True).order_by('sort_order', 'title')

    def lastmod(self, obj):
        return obj.updated_at
