"""
URL configuration for kidurabd project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from apps.storefront.sitemaps import (
    StaticViewSitemap, CategorySitemap, ProductSitemap, PageSitemap
)
from apps.storefront.views.seo_views import robots_txt

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'pages': PageSitemap,
}

urlpatterns = [
    # SEO endpoints
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    path('', include('storefront.urls')),
    path('django-admin/', admin.site.urls),
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('api/v1/', include('kidurabd.api', namespace='api')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'apps.storefront.views.seo_views.custom_404'
handler500 = 'apps.storefront.views.seo_views.custom_500'
