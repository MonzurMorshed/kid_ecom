from django.shortcuts import render, get_object_or_404
from custom_admin.models import Page


class PageView:
    @staticmethod
    def page_detail(request, slug):
        page = get_object_or_404(Page, slug=slug, is_published=True)
        return render(request, 'storefront/page_detail.html', {'page': page})
