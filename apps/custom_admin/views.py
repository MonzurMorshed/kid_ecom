from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from orders.models import Order
from accounts.models import User
from products.models import Product

from .decorators import admin_required
from .forms import AdminRegisterForm, SiteSettingsForm, PaymentMethodForm, HeroSlideForm, BannerForm, AdminEditForm, AdminProfileForm, ChangePasswordForm
from .models import SiteSettings, PaymentMethod, HeroSlide, Banner, AdminProfile, ActivityLog

@admin_required
def dashboard(request):
    total_sales = Order.objects.filter(status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    active_customers = User.objects.filter(is_customer=True, is_blocked=False).count()
    low_stock_products = Product.objects.filter(stock__lt=5)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_customers': active_customers,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'custom_admin/dashboard.html', context)

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if user.is_blocked:
                messages.error(request, "Your admin account has been temporarily blocked.")
                return redirect('custom_admin:login')

            if user.is_staff or user.is_superuser:
                login(request, user)
                ActivityLog.log(request, 'login', f'Admin logged in: {user.username}', target_type='User', target_id=user.pk)
                messages.success(request, f"Welcome back, {user.username}! You have successfully logged in.")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, "Access denied. You do not have admin privileges.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'custom_admin/login.html')

def admin_register(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True
            user.is_customer = False
            user.save()
            messages.success(request, "Admin account successfully created! Please log in.")
            return redirect('custom_admin:login')
    else:
        form = AdminRegisterForm()

    return render(request, 'custom_admin/register.html', {'form': form})

def admin_logout(request):
    ActivityLog.log(request, 'logout', f'Admin logged out: {request.user.username}', target_type='User', target_id=request.user.pk)
    logout(request)
    messages.info(request, "You have been logged out of the admin panel.")
    return redirect('custom_admin:login')


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Admin User List
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_list(request):
    admins = (
        User.objects
        .filter(is_staff=True)
        .annotate(order_count=Count('orders'))
        .order_by('-is_superuser', 'username')
    )
    context = {
        'admins':        admins,
        'total_admins':  admins.count(),
        'superuser_count': admins.filter(is_superuser=True).count(),
    }
    return render(request, 'custom_admin/settings/admin_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Change Password
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current  = form.cleaned_data['current_password']
            new_pwd  = form.cleaned_data['new_password']

            # Verify current password
            if not request.user.check_password(current):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                # Keep the user logged in after password change
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
                return redirect('custom_admin:settings_change_password')
    else:
        form = ChangePasswordForm()

    return render(request, 'custom_admin/settings/change_password.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Promote / Demote Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_role_toggle(request, pk):
    """Toggle is_superuser (Staff -> Superuser or Superuser -> Staff)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can change admin roles.')
        return redirect('custom_admin:settings_admin_list')

    admin = get_object_or_404(User, pk=pk, is_staff=True)

    # Prevent self-demotion
    if admin == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('custom_admin:settings_admin_list')

    if request.method == 'POST':
        admin.is_superuser = not admin.is_superuser
        admin.save(update_fields=['is_superuser'])
        role = 'Superuser' if admin.is_superuser else 'Staff'
        messages.success(request, f'"{admin.username}" is now {role}.')

    return redirect('custom_admin:settings_admin_list')


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Remove Admin (revoke staff access)
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_remove(request, pk):
    """Remove admin privileges (set is_staff=False, is_superuser=False)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can remove admins.')
        return redirect('custom_admin:settings_admin_list')

    admin = get_object_or_404(User, pk=pk, is_staff=True)

    if admin == request.user:
        messages.error(request, 'You cannot remove your own admin access.')
        return redirect('custom_admin:settings_admin_list')

    if request.method == 'POST':
        admin.is_staff       = False
        admin.is_superuser   = False
        admin.save(update_fields=['is_staff', 'is_superuser'])
        messages.success(request, f'Admin access removed for "{admin.username}".')

    return redirect('custom_admin:settings_admin_list')
# ═══════════════════════════════════════════════════════════════════════════════
# SITE SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def site_settings(request):
    """Single-page settings hub — general info, currency, shipping, social, maintenance."""
    settings_obj = SiteSettings.get_settings()

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings saved successfully.')
            return redirect('custom_admin:site_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SiteSettingsForm(instance=settings_obj)

    tabs = [
        ('general',     'General',      '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></circle></svg>'),
        ('currency',    'Currency',     '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'),
        ('shipping',    'Shipping & Tax','<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path></svg>'),
        ('social',      'Social Links', '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>'),
        ('maintenance', 'Maintenance',  '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>'),
    ]

    return render(request, 'custom_admin/settings/site_settings.html', {
        'form': form,
        'settings': settings_obj,
        'tabs': tabs,
    })



# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENT METHODS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def payment_method_list(request):
    """List all configured payment gateways."""
    methods = PaymentMethod.objects.all()
    return render(request, 'custom_admin/settings/payment_methods.html', {
        'methods': methods,
        'active_count': methods.filter(is_active=True).count(),
    })


@admin_required
def payment_method_create(request):
    """Add a new payment gateway."""
    # Determine which gateways are not yet configured
    existing = PaymentMethod.objects.values_list('gateway', flat=True)
    available_choices = [
        (val, label) for val, label in PaymentMethod.GATEWAY_CHOICES
        if val not in existing
    ]

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, request.FILES)
        if form.is_valid():
            method = form.save()
            messages.success(request, f'"{method.display_name}" payment method added.')
            return redirect('custom_admin:payment_method_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentMethodForm()

    # Filter gateway choices to only unconfigured ones
    form.fields['gateway'].choices = [('', '— Select gateway —')] + available_choices

    return render(request, 'custom_admin/settings/payment_method_form.html', {
        'form': form,
        'title': 'Add Payment Method',
        'is_edit': False,
    })


@admin_required
def payment_method_edit(request, pk):
    """Edit an existing payment gateway configuration."""
    method = get_object_or_404(PaymentMethod, pk=pk)

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, request.FILES, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{method.display_name}" updated successfully.')
            return redirect('custom_admin:payment_method_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentMethodForm(instance=method)

    # On edit, lock gateway field to current value
    form.fields['gateway'].disabled = True

    return render(request, 'custom_admin/settings/payment_method_form.html', {
        'form': form,
        'method': method,
        'title': f'Edit — {method.display_name}',
        'is_edit': True,
    })


@admin_required
@require_POST
def payment_method_toggle(request, pk):
    """AJAX: toggle is_active for a payment method."""
    method = get_object_or_404(PaymentMethod, pk=pk)
    method.is_active = not method.is_active
    method.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': method.is_active})


@admin_required
@require_POST
def payment_method_delete(request, pk):
    """Delete a payment method."""
    method = get_object_or_404(PaymentMethod, pk=pk)
    name = method.display_name
    method.delete()
    messages.success(request, f'"{name}" has been removed.')
    return redirect('custom_admin:payment_method_list')


# ═══════════════════════════════════════════════════════════════════════════════
# HERO SLIDER
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# BANNERS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'custom_admin/content/banner_list.html', {
        'banners': banners,
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
    title = banner.title
    banner.delete()
    messages.success(request, f'Banner "{title}" deleted.')
    return redirect('custom_admin:banner_list')


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def admin_user_list(request):
    """List all staff/superuser accounts with their roles."""
    admins = User.objects.filter(is_staff=True).select_related('admin_profile').order_by('username')
    # Ensure every staff user has a profile
    for u in admins:
        AdminProfile.get_or_create_for(u)
    admins = User.objects.filter(is_staff=True).select_related('admin_profile').order_by('username')
    return render(request, 'custom_admin/admin_users/user_list.html', {
        'admins': admins,
    })


@admin_required
def admin_user_edit(request, pk):
    """Edit name, email, active status and role of an admin account."""
    target = get_object_or_404(User, pk=pk, is_staff=True)
    profile = AdminProfile.get_or_create_for(target)

    user_form    = AdminEditForm(request.POST or None, instance=target)
    profile_form = AdminProfileForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            ActivityLog.log(
                request, 'update',
                f'Updated admin account: {target.username}',
                target_type='User', target_id=target.pk
            )
            messages.success(request, f'Admin "{target.username}" updated successfully.')
            return redirect('custom_admin:admin_user_list')
        messages.error(request, 'Please fix the errors below.')

    return render(request, 'custom_admin/admin_users/user_edit.html', {
        'target':       target,
        'user_form':    user_form,
        'profile_form': profile_form,
        'title':        f'Edit Admin — {target.username}',
    })


@admin_required
@require_POST
def admin_user_toggle(request, pk):
    """AJAX: enable / disable an admin account."""
    target = get_object_or_404(User, pk=pk, is_staff=True)
    if target == request.user:
        return JsonResponse({'error': 'Cannot disable your own account.'}, status=400)
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    ActivityLog.log(
        request,
        'toggle',
        f'Admin account {"enabled" if target.is_active else "disabled"}: {target.username}',
        target_type='User', target_id=target.pk
    )
    return JsonResponse({'status': 'ok', 'is_active': target.is_active})


# ═══════════════════════════════════════════════════════════════════════════════
# CHANGE PASSWORD
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def change_password(request, pk=None):
    """
    Change password:
    - If pk is None  => change own password (requires current_password).
    - If pk is given => superadmin changing someone else's password (no current_password check).
    """
    is_self = pk is None
    target  = request.user if is_self else get_object_or_404(User, pk=pk, is_staff=True)

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_pw  = form.cleaned_data.get('current_password')
            new_pw      = form.cleaned_data['new_password']

            # When changing own password, verify the current one
            if is_self and not target.check_password(current_pw):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                target.set_password(new_pw)
                target.save()
                ActivityLog.log(
                    request, 'password',
                    f'Password changed for: {target.username}',
                    target_type='User', target_id=target.pk
                )
                if is_self:
                    # Re-login so session stays valid
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, target)
                    messages.success(request, 'Your password has been updated.')
                    return redirect('custom_admin:dashboard')
                else:
                    messages.success(request, f'Password for "{target.username}" reset successfully.')
                    return redirect('custom_admin:admin_user_list')
    else:
        form = ChangePasswordForm()

    return render(request, 'custom_admin/admin_users/change_password.html', {
        'form':    form,
        'target':  target,
        'is_self': is_self,
        'title':   'Change My Password' if is_self else f'Reset Password — {target.username}',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def activity_log(request):
    """Paginated activity audit log with action + actor filters."""
    from django.core.paginator import Paginator

    qs = ActivityLog.objects.select_related('actor').all()

    # Filters
    action_filter = request.GET.get('action', '')
    actor_filter  = request.GET.get('actor', '')
    search        = request.GET.get('q', '').strip()

    if action_filter:
        qs = qs.filter(action=action_filter)
    if actor_filter:
        qs = qs.filter(actor__username__icontains=actor_filter)
    if search:
        qs = qs.filter(description__icontains=search)

    paginator = Paginator(qs, 50)
    page      = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'custom_admin/admin_users/activity_log.html', {
        'page':           page,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'action_filter':  action_filter,
        'actor_filter':   actor_filter,
        'search':         search,
    })


@admin_required
@require_POST
def activity_log_clear(request):
    """Delete all activity logs (superadmin only)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can clear the activity log.')
        return redirect('custom_admin:activity_log')
    ActivityLog.objects.all().delete()
    messages.success(request, 'Activity log cleared.')
    return redirect('custom_admin:activity_log')


# ═══════════════════════════════════════════════════════════════════════════════
# FORGOT / RESET PASSWORD  (admin-only, token-based)
# ═══════════════════════════════════════════════════════════════════════════════

_token_generator = PasswordResetTokenGenerator()


def admin_forgot_password(request):
    """Step 1 — accept email, validate it belongs to a staff user, send reset link."""
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        # Always show the same success message to prevent user enumeration
        success_msg = (
            'If that email belongs to an admin account, '
            'a password reset link has been sent. Check your inbox (or the server console in development).'
        )

        user = User.objects.filter(email__iexact=email, is_staff=True).first()
        if user:
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = _token_generator.make_token(user)

            # Build the full reset URL
            scheme   = 'https' if request.is_secure() else 'http'
            host     = request.get_host()
            reset_url = f'{scheme}://{host}/admin/reset-password/{uid}/{token}/'

            # Build email body
            subject = 'Kidurabd Admin — Password Reset Request'
            body = (
                f'Hi {user.username},\n\n'
                f'A password reset was requested for your admin account.\n\n'
                f'Click the link below to set a new password (valid for 1 hour):\n'
                f'{reset_url}\n\n'
                f'If you did not request this, you can safely ignore this email.\n\n'
                f'— Kidurabd Admin'
            )

            send_mail(
                subject,
                body,
                getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'admin@kidurabd.com'),
                [user.email],
                fail_silently=True,
            )

            ActivityLog.log(
                request, 'password',
                f'Password reset requested for: {user.username} ({user.email})',
                target_type='User', target_id=user.pk
            )

        messages.success(request, success_msg)
        return redirect('custom_admin:forgot_password')

    return render(request, 'custom_admin/forgot_password.html')


def admin_reset_password(request, uidb64, token):
    """Step 2 — validate token, show new-password form, save."""
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    # Decode user
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_staff=True)
    except (User.DoesNotExist, ValueError, OverflowError, TypeError):
        user = None

    # Validate token
    if user is None or not _token_generator.check_token(user, token):
        return render(request, 'custom_admin/reset_password_invalid.html')

    if request.method == 'POST':
        new_pw      = request.POST.get('new_password', '')
        confirm_pw  = request.POST.get('confirm_password', '')
        error       = None

        if len(new_pw) < 8:
            error = 'Password must be at least 8 characters.'
        elif new_pw != confirm_pw:
            error = 'Passwords do not match.'

        if error:
            return render(request, 'custom_admin/reset_password_form.html', {
                'error': error, 'uidb64': uidb64, 'token': token, 'username': user.username
            })

        user.set_password(new_pw)
        user.save()
        ActivityLog.log(
            request, 'password',
            f'Password reset completed for: {user.username}',
            target_type='User', target_id=user.pk
        )
        messages.success(request, f'Password for "{user.username}" has been reset. Please log in.')
        return redirect('custom_admin:login')

    return render(request, 'custom_admin/reset_password_form.html', {
        'uidb64': uidb64, 'token': token, 'username': user.username
    })

@admin_required
def customer_list(request):
    qs = (
        User.objects
        .filter(is_staff=False, is_superuser=False)
        .annotate(order_count=Count('orders'))
        .order_by('-id')
    )

    # ── Search ──
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone_number__icontains=q)
        )

    # ── Status filter ──
    status = request.GET.get('status', '').strip()
    if status == 'active':
        qs = qs.filter(is_blocked=False)
    elif status == 'blocked':
        qs = qs.filter(is_blocked=True)

    # ── Summary counts (always on full customer base) ──
    total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
    active_count    = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=False).count()
    blocked_count   = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=True).count()

    # ── Pagination ──
    paginator   = Paginator(qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'customers':       page_obj,
        'total_customers': total_customers,
        'active_count':    active_count,
        'blocked_count':   blocked_count,
        'q':               q,
        'status':          status,
    }
    return render(request, 'custom_admin/customers/customer_list.html', context)


@admin_required
def customer_detail(request, pk):
    customer = get_object_or_404(
        User.objects.annotate(order_count=Count('orders')),
        pk=pk, is_staff=False, is_superuser=False
    )
    orders = customer.orders.order_by('-created_at')
    total_spent = orders.filter(status='DELIVERED').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    context = {
        'customer':    customer,
        'orders':      orders,
        'total_spent': total_spent,
    }
    return render(request, 'custom_admin/customers/customer_detail.html', context)


@admin_required
@require_POST
def customer_block_toggle(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False, is_superuser=False)
    customer.is_blocked = not customer.is_blocked
    customer.save(update_fields=['is_blocked'])
    action = 'blocked' if customer.is_blocked else 'unblocked'
    messages.success(request, f'Customer "{customer.username}" has been {action}.')
    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('custom_admin:customer_detail', pk=pk)

