from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from ..decorators import admin_required
from ..forms import HeroSlideForm, BannerForm
from ..models import HeroSlide, Banner


# ── Hero Slider ───────────────────────────────────────────────────────────────

@admin_required
def slider_list(request):
    slides = HeroSlide.objects.all()
    return render(request, 'custom_admin/content/slider_list.html', {'slides': slides})


@admin_required
def slider_create(request):
    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save()
            messages.success(request, f'Slide "{slide.title}" created successfully.')
            return redirect('custom_admin:slider_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = HeroSlideForm()
    return render(request, 'custom_admin/content/slide_form.html', {
        'form': form, 'title': 'Add New Slide', 'is_edit': False,
    })


@admin_required
def slider_edit(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, f'Slide "{slide.title}" updated.')
            return redirect('custom_admin:slider_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = HeroSlideForm(instance=slide)
    return render(request, 'custom_admin/content/slide_form.html', {
        'form': form, 'slide': slide, 'title': f'Edit — {slide.title}', 'is_edit': True,
    })


@admin_required
@require_POST
def slider_toggle(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    slide.is_active = not slide.is_active
    slide.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': slide.is_active})


@admin_required
@require_POST
def slider_delete(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    title = slide.title
    slide.delete()
    messages.success(request, f'Slide "{title}" deleted.')
    return redirect('custom_admin:slider_list')


# ── Banners ───────────────────────────────────────────────────────────────────

@admin_required
def banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'custom_admin/content/banner_list.html', {
        'banners':          banners,
        'position_choices': Banner.POSITION_CHOICES,
    })


@admin_required
def banner_create(request):
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner.title}" created.')
            return redirect('custom_admin:banner_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = BannerForm()
    return render(request, 'custom_admin/content/banner_form.html', {
        'form': form, 'title': 'Add New Banner', 'is_edit': False,
    })


@admin_required
def banner_edit(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, f'Banner "{banner.title}" updated.')
            return redirect('custom_admin:banner_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = BannerForm(instance=banner)
    return render(request, 'custom_admin/content/banner_form.html', {
        'form': form, 'banner': banner, 'title': f'Edit — {banner.title}', 'is_edit': True,
    })


@admin_required
@require_POST
def banner_toggle(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.is_active = not banner.is_active
    banner.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': banner.is_active})


@admin_required
@require_POST
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    title  = banner.title
    banner.delete()
    messages.success(request, f'Banner "{title}" deleted.')
    return redirect('custom_admin:banner_list')
