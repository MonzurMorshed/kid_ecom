from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from django.conf import settings
from django.db.models import Count, Q
from accounts.models import User
from axes.models import AccessAttempt, AccessFailureLog
from axes.utils import reset as axes_reset
from ..decorators import admin_required
from ..forms import AdminEditForm, AdminProfileForm, ChangePasswordForm
from ..models import ActivityLog, AdminProfile


# ── Admin User List ───────────────────────────────────────────────────────────

@admin_required
def admin_user_list(request):
    """List all staff/superuser accounts with their roles."""
    admins = User.objects.filter(is_staff=True).select_related('admin_profile').order_by('username')
    for u in admins:
        AdminProfile.get_or_create_for(u)
    admins = User.objects.filter(is_staff=True).select_related('admin_profile').order_by('username')
    return render(request, 'custom_admin/admin_users/user_list.html', {'admins': admins})


# ── Admin User Edit ───────────────────────────────────────────────────────────

@admin_required
def admin_user_edit(request, pk):
    """Edit name, email, active status and role of an admin account."""
    target  = get_object_or_404(User, pk=pk, is_staff=True)
    profile = AdminProfile.get_or_create_for(target)

    user_form    = AdminEditForm(request.POST or None, instance=target)
    profile_form = AdminProfileForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            ActivityLog.log(request, 'update', f'Updated admin account: {target.username}', target_type='User', target_id=target.pk)
            messages.success(request, f'Admin "{target.username}" updated successfully.')
            return redirect('custom_admin:admin_user_list')
        messages.error(request, 'Please fix the errors below.')

    return render(request, 'custom_admin/admin_users/user_edit.html', {
        'target':       target,
        'user_form':    user_form,
        'profile_form': profile_form,
        'title':        f'Edit Admin — {target.username}',
    })


# ── Admin User Toggle (AJAX) ──────────────────────────────────────────────────

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
        request, 'toggle',
        f'Admin account {"enabled" if target.is_active else "disabled"}: {target.username}',
        target_type='User', target_id=target.pk
    )
    return JsonResponse({'status': 'ok', 'is_active': target.is_active})


# ── Change / Reset Password ───────────────────────────────────────────────────

@admin_required
def change_password(request, pk=None):
    """
    Change password:
    - pk=None  => change own password (requires current_password).
    - pk given => superadmin changing someone else's password (no current_password check).
    """
    is_self = pk is None
    target  = request.user if is_self else get_object_or_404(User, pk=pk, is_staff=True)

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_pw = form.cleaned_data.get('current_password')
            new_pw     = form.cleaned_data['new_password']

            if is_self and not target.check_password(current_pw):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                target.set_password(new_pw)
                target.save()
                ActivityLog.log(request, 'password', f'Password changed for: {target.username}', target_type='User', target_id=target.pk)
                if is_self:
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


# ── Activity Log ──────────────────────────────────────────────────────────────

@admin_required
def activity_log(request):
    """Paginated activity audit log with action + actor filters."""
    qs = ActivityLog.objects.select_related('actor').all()

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


# ── Legacy Settings Admin Views (backwards compatibility) ─────────────────────

@admin_required
def settings_admin_list(request):
    admins = (
        User.objects
        .filter(is_staff=True)
        .annotate(order_count=Count('orders'))
        .order_by('-is_superuser', 'username')
    )
    context = {
        'admins':          admins,
        'total_admins':    admins.count(),
        'superuser_count': admins.filter(is_superuser=True).count(),
    }
    return render(request, 'custom_admin/settings/admin_list.html', context)


@admin_required
def settings_change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current = form.cleaned_data['current_password']
            new_pwd = form.cleaned_data['new_password']

            if not request.user.check_password(current):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
                return redirect('custom_admin:settings_change_password')
    else:
        form = ChangePasswordForm()

    return render(request, 'custom_admin/settings/change_password.html', {'form': form})


@admin_required
def settings_admin_role_toggle(request, pk):
    """Toggle is_superuser (Staff -> Superuser or Superuser -> Staff)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can change admin roles.')
        return redirect('custom_admin:settings_admin_list')

    admin = get_object_or_404(User, pk=pk, is_staff=True)
    if admin == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('custom_admin:settings_admin_list')

    if request.method == 'POST':
        admin.is_superuser = not admin.is_superuser
        admin.save(update_fields=['is_superuser'])
        role = 'Superuser' if admin.is_superuser else 'Staff'
        messages.success(request, f'"{admin.username}" is now {role}.')

    return redirect('custom_admin:settings_admin_list')


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
        admin.is_staff     = False
        admin.is_superuser = False
        admin.save(update_fields=['is_staff', 'is_superuser'])
        messages.success(request, f'Admin access removed for "{admin.username}".')

    return redirect('custom_admin:settings_admin_list')


# ── Locked Users / Brute Force Security ──────────────────────────────────────

@admin_required
def locked_users_list(request):
    """Monitor active login attempts and locked-out users/IPs."""
    limit = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
    cooloff = getattr(settings, 'AXES_COOLOFF_TIME', 0.5)

    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = AccessAttempt.objects.all().order_by('-attempt_time')

    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(ip_address__icontains=search))

    if status_filter == 'locked':
        qs = qs.filter(failures_since_start__gte=limit)
    elif status_filter == 'warning':
        qs = qs.filter(failures_since_start__lt=limit)

    total_attempts = AccessAttempt.objects.count()
    locked_count = AccessAttempt.objects.filter(failures_since_start__gte=limit).count()
    warning_count = total_attempts - locked_count

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page', 1))

    # Recent failure logs
    failure_logs = AccessFailureLog.objects.all().order_by('-attempt_time')[:30]

    return render(request, 'custom_admin/admin_users/locked_users.html', {
        'page': page,
        'search': search,
        'status_filter': status_filter,
        'failure_limit': limit,
        'cooloff_hours': cooloff,
        'total_attempts': total_attempts,
        'locked_count': locked_count,
        'warning_count': warning_count,
        'failure_logs': failure_logs,
    })


@admin_required
@require_POST
def locked_user_unlock(request, pk):
    """Unlock a specific access attempt / locked account."""
    attempt = get_object_or_404(AccessAttempt, pk=pk)
    username = attempt.username or ''
    ip = attempt.ip_address or ''

    # Reset axes attempt
    if username or ip:
        axes_reset(username=username if username else None, ip=ip if ip else None)
    else:
        attempt.delete()

    ActivityLog.log(
        request, 'update',
        f'Unlocked login attempt for: {username or "unknown"} (IP: {ip or "unknown"})',
        target_type='AccessAttempt',
        target_id=pk,
    )
    messages.success(request, f'Lockout cleared for "{username or ip}". User can now sign in.')
    return redirect('custom_admin:locked_users_list')


@admin_required
@require_POST
def locked_users_reset_all(request):
    """Reset all active login lockouts and attempts."""
    count = AccessAttempt.objects.count()
    axes_reset()
    ActivityLog.log(
        request, 'update',
        f'Reset all {count} active login lockout attempts',
        target_type='AccessAttempt',
    )
    messages.success(request, f'All login lockouts ({count} attempts) have been successfully reset.')
    return redirect('custom_admin:locked_users_list')

