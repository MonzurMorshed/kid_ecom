from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from ..decorators import admin_required, permission_required
from ..forms import SiteSettingsForm, PaymentMethodForm, ThemeSettingsForm
from ..models import SiteSettings, PaymentMethod


# ── Site Settings ─────────────────────────────────────────────────────────────

@permission_required('settings')
def site_settings(request):
    """Single-page settings hub — general info, currency, shipping, social."""
    import logging
    logger = logging.getLogger('django.request')

    try:
        settings_obj = SiteSettings.get_settings()
    except Exception as e:
        logger.error(f'Error getting SiteSettings: {e}', exc_info=True)
        settings_obj = SiteSettings(pk=1, site_name='Kidurabd')

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Site settings saved successfully.')
                return redirect('custom_admin:site_settings')
            except Exception as e:
                logger.error(f'Error saving site settings: {e}', exc_info=True)
                messages.error(request, f'Failed to save settings: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        try:
            form = SiteSettingsForm(instance=settings_obj)
        except Exception as e:
            logger.error(f'Error initializing SiteSettingsForm: {e}', exc_info=True)
            form = SiteSettingsForm()

    tabs = [
        ('general',     'General',       '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></circle></svg>'),
        ('currency',    'Currency',      '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'),
        ('shipping',    'Shipping & Tax','<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path></svg>'),
        ('social',      'Social Links',  '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>'),
    ]

    return render(request, 'custom_admin/settings/site_settings.html', {
        'form':     form,
        'settings': settings_obj,
        'tabs':     tabs,
    })


# ── Theme Settings ────────────────────────────────────────────────────────────

@permission_required('settings')
def theme_settings(request):
    """
    Dedicated visual theme customizer:
    - Store background & text colors
    - Primary & secondary brand accent colors
    - Header layout (Classic, Centered, Compact) & colors
    - Header sticky & border toggles
    - Announcement bar message, visibility & colors
    - Footer layout (Classic 4-col, Centered Modern, Minimal) & colors
    - Card & component roundness
    """
    import logging
    logger = logging.getLogger('django.request')

    try:
        settings_obj = SiteSettings.get_settings()
    except Exception as e:
        logger.error(f'Error getting SiteSettings in theme_settings: {e}', exc_info=True)
        settings_obj = SiteSettings(pk=1, site_name='Kidurabd')

    if request.method == 'POST':
        form = ThemeSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Theme settings updated successfully! Storefront has been styled.')
                return redirect('custom_admin:theme_settings')
            except Exception as e:
                logger.error(f'Error saving theme settings: {e}', exc_info=True)
                messages.error(request, f'Failed to save theme settings: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ThemeSettingsForm(instance=settings_obj)

    return render(request, 'custom_admin/settings/theme_settings.html', {
        'form': form,
        'settings': settings_obj,
    })


# ── Payment Methods ───────────────────────────────────────────────────────────

@permission_required('payment_methods')
def payment_method_list(request):
    """List all configured payment gateways."""
    methods = PaymentMethod.objects.all()
    return render(request, 'custom_admin/settings/payment_methods.html', {
        'methods':      methods,
        'active_count': methods.filter(is_active=True).count(),
    })


@permission_required('payment_methods')
def payment_method_create(request):
    """Add a new payment gateway."""
    existing          = PaymentMethod.objects.values_list('gateway', flat=True)
    available_choices = [(val, label) for val, label in PaymentMethod.GATEWAY_CHOICES if val not in existing]

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, request.FILES)
        if form.is_valid():
            method = form.save()
            messages.success(request, f'"{method.display_name}" payment method added.')
            return redirect('custom_admin:payment_method_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentMethodForm()

    form.fields['gateway'].choices = [('', '— Select gateway —')] + available_choices
    return render(request, 'custom_admin/settings/payment_method_form.html', {
        'form': form, 'title': 'Add Payment Method', 'is_edit': False,
    })


@permission_required('payment_methods')
def payment_method_edit(request, pk):
    """Edit an existing payment gateway configuration."""
    method = get_object_or_404(PaymentMethod, pk=pk)

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, request.FILES, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{method.display_name}" updated successfully.')
            return redirect('custom_admin:payment_method_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentMethodForm(instance=method)

    form.fields['gateway'].disabled = True
    return render(request, 'custom_admin/settings/payment_method_form.html', {
        'form': form, 'method': method, 'title': f'Edit — {method.display_name}', 'is_edit': True,
    })


@permission_required('payment_methods')
@require_POST
def payment_method_toggle(request, pk):
    """AJAX: toggle is_active for a payment method."""
    method = get_object_or_404(PaymentMethod, pk=pk)
    method.is_active = not method.is_active
    method.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': method.is_active})


@permission_required('payment_methods')
@require_POST
def payment_method_delete(request, pk):
    """Delete a payment method."""
    method = get_object_or_404(PaymentMethod, pk=pk)
    name   = method.display_name
    method.delete()
    messages.success(request, f'"{name}" has been removed.')
    return redirect('custom_admin:payment_method_list')


@permission_required('developer')
@require_POST
def clear_cache(request):
    """
    Clears:
    1. Django in-memory cache (cache.clear())
    2. Touches tmp/restart.txt to prompt CloudLinux / Passenger to reload Python workers
    3. Writes an entry in ActivityLog
    """
    from django.core.cache import cache
    from django.conf import settings
    from ..models import ActivityLog

    # 1. Clear Django cache
    try:
        cache.clear()
    except Exception:
        pass

    # 2. Touch restart.txt for cPanel / Passenger reload
    try:
        restart_file = settings.BASE_DIR / 'tmp' / 'restart.txt'
        restart_file.parent.mkdir(parents=True, exist_ok=True)
        restart_file.touch()
    except Exception:
        pass

    # 3. Log to activity log
    try:
        ActivityLog.log(
            request=request,
            action='settings',
            description='Cleared server cache and reloaded application.',
            target_type='System Cache',
        )
    except Exception:
        pass

    messages.success(request, 'Server cache cleared and application reloaded successfully!')

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('custom_admin:dashboard')

