"""
URL configuration for kidurabd project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='custom_admin:dashboard', permanent=False)),
    path('django-admin/', admin.site.urls),
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
