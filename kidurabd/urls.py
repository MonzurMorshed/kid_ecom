"""
URL configuration for kidurabd project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap

from storefront.sitemaps import (
    StaticViewSitemap, CategorySitemap, ProductSitemap, PageSitemap
)
from storefront.views.seo_views import robots_txt

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'pages': PageSitemap,
}

from django.utils.cache import patch_cache_control

def cached_media_serve(request, path, document_root=None, show_indexes=False):
    response = serve(request, path, document_root, show_indexes)
    patch_cache_control(response, public=True, max_age=2592000, immutable=True)
    return response

urlpatterns = [
    # SEO endpoints
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    path('', include('storefront.urls')),
    path('django-admin/', admin.site.urls),
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('api/v1/', include('kidurabd.api', namespace='api')),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Media files (served with 30-day browser caching headers)
    re_path(r'^media/(?P<path>.*)$', cached_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

handler404 = 'storefront.views.seo_views.custom_404'
handler500 = 'storefront.views.seo_views.custom_500'
