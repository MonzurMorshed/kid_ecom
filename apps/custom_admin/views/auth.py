from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from accounts.models import User
from ..forms import AdminRegisterForm
from ..models import ActivityLog, AdminProfile
from ..permissions import ALL_PERMISSION_IDS, DEFAULT_ROLE_PERMISSIONS

_token_generator = PasswordResetTokenGenerator()


# ── Auth: Login / Register / Logout ──────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if getattr(user, 'is_blocked', False):
                messages.error(request, 'Your admin account has been temporarily blocked.')
                return redirect('custom_admin:login')

            if not user.is_active:
                messages.error(request, 'Your account is currently disabled. Please contact the Super Admin.')
                return redirect('custom_admin:login')

            if user.is_staff or user.is_superuser:
                login(request, user)

                # Ensure AdminProfile and role are synchronized
                profile = AdminProfile.get_or_create_for(user)
                if user.is_superuser and profile.role != 'superadmin':
                    profile.role = 'superadmin'
                    profile.permissions = list(ALL_PERMISSION_IDS)
                    profile.save()
                elif not profile.role:
                    profile.role = 'staff'
                    profile.permissions = list(DEFAULT_ROLE_PERMISSIONS['staff'])
                    profile.save()

                ActivityLog.log(
                    request, 'login',
                    f'Admin logged in: {user.username} ({profile.get_role_display()})',
                    target_type='User', target_id=user.pk
                )
                messages.success(request, f'Welcome back, {user.username}! Logged in as {profile.get_role_display()}.')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, 'Access denied. You do not have staff/admin privileges.')
        else:
            # Check if user credentials match an inactive staff account awaiting Super Admin activation
            potential_user = User.objects.filter(username=username_input).first() or User.objects.filter(email=username_input).first()
            if potential_user and potential_user.check_password(password_input):
                if not potential_user.is_active:
                    messages.warning(
                        request,
                        f'Staff account "{potential_user.username}" is pending Super Admin review & activation. '
                        f'You will be able to log in as soon as the administrator reviews and activates your account.'
                    )
                    return redirect('custom_admin:login')
                if getattr(potential_user, 'is_blocked', False):
                    messages.error(request, 'Your admin account has been temporarily blocked.')
                    return redirect('custom_admin:login')
            messages.error(request, 'Invalid username or password.')

    return render(request, 'custom_admin/login.html')


def admin_register(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff    = True
            user.is_customer = False
            user.is_active   = False  # Inactive until reviewed & activated by Super Admin
            user.save()

            # Assign default 'staff' role with default staff permissions
            profile = AdminProfile.get_or_create_for(user)
            profile.role = 'staff'
            profile.permissions = list(DEFAULT_ROLE_PERMISSIONS['staff'])
            profile.save()

            # Send email alert to Super Admins
            from ..emails import send_new_staff_registration_alert
            send_new_staff_registration_alert(user, request)

            ActivityLog.log(
                request, 'create',
                f'New staff account registered (pending Super Admin activation): {user.username}',
                actor=user, target_type='User', target_id=user.pk
            )
            messages.success(
                request,
                f'Registration successful! Staff account for "{user.username}" has been submitted for review. '
                f'The Super Admin has been notified by email and will activate your account soon.'
            )
            return redirect('custom_admin:login')
    else:
        form = AdminRegisterForm()

    return render(request, 'custom_admin/register.html', {'form': form})


def admin_logout(request):
    ActivityLog.log(request, 'logout', f'Admin logged out: {request.user.username}', target_type='User', target_id=request.user.pk)
    logout(request)
    messages.info(request, 'You have been logged out of the admin panel.')
    return redirect('custom_admin:login')


# ── Auth: Forgot / Reset Password ────────────────────────────────────────────

def admin_forgot_password(request):
    """Step 1 — accept email, validate it belongs to a staff user, send reset link."""
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        success_msg = (
            'If that email belongs to an admin account, '
            'a password reset link has been sent. Check your inbox (or the server console in development).'
        )

        user = User.objects.filter(email__iexact=email, is_staff=True).first()
        if user:
            uid       = urlsafe_base64_encode(force_bytes(user.pk))
            token     = _token_generator.make_token(user)
            scheme    = 'https' if request.is_secure() else 'http'
            host      = request.get_host()
            reset_url = f'{scheme}://{host}/admin/reset-password/{uid}/{token}/'

            from kidurabd.email_service import send_templated_email
            send_templated_email(
                channel='notification',
                subject='Kidurabd Admin — Password Reset Request',
                template_name='emails/password_reset.html',
                context={
                    'user_display': user.username,
                    'email': user.email,
                    'reset_url': reset_url,
                },
                to=user.email,
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

    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_staff=True)
    except (User.DoesNotExist, ValueError, OverflowError, TypeError):
        user = None

    if user is None or not _token_generator.check_token(user, token):
        return render(request, 'custom_admin/reset_password_invalid.html')

    if request.method == 'POST':
        new_pw     = request.POST.get('new_password', '')
        confirm_pw = request.POST.get('confirm_password', '')
        error      = None

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
