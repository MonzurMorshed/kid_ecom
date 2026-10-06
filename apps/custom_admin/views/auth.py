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
from ..models import ActivityLog

_token_generator = PasswordResetTokenGenerator()


# ── Auth: Login / Register / Logout ──────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if user.is_blocked:
                messages.error(request, 'Your admin account has been temporarily blocked.')
                return redirect('custom_admin:login')
            if user.is_staff or user.is_superuser:
                login(request, user)
                ActivityLog.log(request, 'login', f'Admin logged in: {user.username}', target_type='User', target_id=user.pk)
                messages.success(request, f'Welcome back, {user.username}! You have successfully logged in.')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, 'Access denied. You do not have admin privileges.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'custom_admin/login.html')


def admin_register(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff    = True
            user.is_customer = False
            user.save()
            messages.success(request, 'Admin account successfully created! Please log in.')
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

            subject = 'Kidurabd Admin — Password Reset Request'
            body    = (
                f'Hi {user.username},\n\n'
                f'A password reset was requested for your admin account.\n\n'
                f'Click the link below to set a new password (valid for 1 hour):\n'
                f'{reset_url}\n\n'
                f'If you did not request this, you can safely ignore this email.\n\n'
                f'— Kidurabd Admin'
            )
            send_mail(
                subject, body,
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
