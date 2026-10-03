from django.http import HttpResponse
from django.shortcuts import render


def robots_txt(request):
    """Generate dynamic robots.txt matching domain and sitemap location."""
    scheme = request.scheme
    host = request.get_host()
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /accounts/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /api/",
        "",
        f"Sitemap: {scheme}://{host}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def custom_404(request, exception=None):
    """Render friendly branded 404 Not Found error page."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Render friendly branded 500 Server Error page."""
    return render(request, '500.html', status=500)
