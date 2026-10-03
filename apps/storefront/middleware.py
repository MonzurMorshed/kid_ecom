"""
Maintenance mode middleware.

When SiteSettings.maintenance_mode is True, all non-admin requests receive a
503 Service Unavailable response rendered with the maintenance.html template.
Admin users (is_staff=True) bypass maintenance mode so they can still access
both the custom admin panel and the storefront.
"""
from django.http import HttpResponse
from django.template.loader import render_to_string


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass for admin users
        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        # Bypass for the admin URL prefix (custom_admin) so staff can log in
        if request.path.startswith('/admin-panel/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            from custom_admin.models import SiteSettings
            settings_obj = SiteSettings.get_settings()
            if settings_obj.maintenance_mode:
                html = render_to_string('storefront/maintenance.html', {
                    'maintenance_msg': settings_obj.maintenance_msg,
                    'site_name': settings_obj.site_name,
                })
                return HttpResponse(html, status=503)
        except Exception:
            pass  # If DB is unavailable, proceed normally

        return self.get_response(request)
