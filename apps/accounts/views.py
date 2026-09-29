from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from functools import wraps

from .models import User
from .forms import (
    CustomerRegisterForm, CustomerLoginForm, CustomerProfileForm,
    CustomerChangePasswordForm, CustomerForgotPasswordForm, CustomerResetPasswordForm,
)


# ── Auth decorators ───────────────────────────────────────────────────────────

def customer_required(view_func):
    """Redirect to login if not a logged-in customer."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_staff or request.user.is_superuser:
            messages.info(request, 'Please log in to access that page.')
            return redirect('accounts:login')
        if request.user.is_blocked:
            logout(request)
            messages.error(request, 'Your account has been suspended. Please contact support.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def guest_only(view_func):
    """Redirect logged-in customers to their profile."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('custom_admin:dashboard')
            return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ──────────────────────────────────────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def register_view(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Kidurabd, {user.first_name}! 🎉')
            return redirect(request.GET.get('next') or 'storefront:index')
    else:
        form = CustomerRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def login_view(request):
    form = CustomerLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email'].lower()
        password = form.cleaned_data['password']
        remember = form.cleaned_data.get('remember_me', False)

        # Try authenticate by email (username = email)
        user = authenticate(request, username=email, password=password)
        if user is None:
            # Fallback: look up by email field in case username differs
            try:
                u = User.objects.get(email__iexact=email)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            if user.is_blocked:
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return redirect('accounts:login')
            login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Session cookie expires when browser closes
            if user.is_staff or user.is_superuser:
                return redirect('custom_admin:dashboard')
            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            return redirect(request.GET.get('next') or 'storefront:index')
        else:
            messages.error(request, 'No account found with that email and password.')

    return render(request, 'accounts/login.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out. See you soon!')
    return redirect('accounts:login')


# ──────────────────────────────────────────────────────────────────────────────
# Profile — view & edit
# ──────────────────────────────────────────────────────────────────────────────
@customer_required
def profile_view(request):
    user = request.user
    orders = user.orders.order_by('-created_at')[:5]
    total_spent = user.orders.filter(status='DELIVERED').aggregate(t=Sum('total_amount'))['t'] or 0
    return render(request, 'accounts/profile.html', {
        'customer': user,
        'recent_orders': orders,
        'total_spent': total_spent,
    })


@customer_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=user)
        if form.is_valid():
            profile = form.save(commit=False)
            # Keep username in sync with email
            profile.username = form.cleaned_data['email'].lower()
            profile.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = CustomerProfileForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Change Password
# ──────────────────────────────────────────────────────────────────────────────
@customer_required
def change_password_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomerChangePasswordForm(request.POST)
        if form.is_valid():
            if not user.check_password(form.cleaned_data['current_password']):
                form.add_error('current_password', 'Your current password is incorrect.')
            else:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)   # keep user logged in
                messages.success(request, 'Password changed successfully.')
                return redirect('accounts:profile')
    else:
        form = CustomerChangePasswordForm()
    return render(request, 'accounts/change_password.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Forgot Password
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def forgot_password_view(request):
    if request.method == 'POST':
        form = CustomerForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            try:
                user = User.objects.get(email__iexact=email, is_staff=False, is_superuser=False)
                token_gen = PasswordResetTokenGenerator()
                uid   = urlsafe_base64_encode(force_bytes(user.pk))
                token = token_gen.make_token(user)
                reset_url = request.build_absolute_uri(
                    f'/accounts/reset-password/{uid}/{token}/'
                )
                # Send email (prints to console in dev)
                send_mail(
                    subject='Reset your Kidurabd password',
                    message=f'Hello {user.first_name},\n\nClick this link to reset your password:\n{reset_url}\n\nThis link expires in 1 hour.\n\n— Kidurabd',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kidurabd.com'),
                    recipient_list=[email],
                    fail_silently=True,
                )
            except User.DoesNotExist:
                pass   # Don't reveal whether the email exists
            # Always show the same success message for security
            messages.success(request, 'If an account exists for that email, we sent a password reset link.')
            return redirect('accounts:forgot_password')
    else:
        form = CustomerForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Reset Password
# ──────────────────────────────────────────────────────────────────────────────
def reset_password_view(request, uidb64, token):
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_gen = PasswordResetTokenGenerator()
    if user is None or not token_gen.check_token(user, token):
        return render(request, 'accounts/reset_password_invalid.html')

    if request.method == 'POST':
        form = CustomerResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, 'Your password has been reset. Please log in.')
            return redirect('accounts:login')
    else:
        form = CustomerResetPasswordForm()
    return render(request, 'accounts/reset_password.html', {'form': form, 'uid': uidb64, 'token': token})


# ──────────────────────────────────────────────────────────────────────────────
# Admin — Customer List (used by custom_admin)
# ──────────────────────────────────────────────────────────────────────────────
def customer_list(request):
    qs = (
        User.objects
        .filter(is_staff=False, is_superuser=False)
        .annotate(order_count=Count('orders'))
        .order_by('-id')
    )
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q) |
            Q(phone_number__icontains=q)
        )
    status = request.GET.get('status', '').strip()
    if status == 'active':
        qs = qs.filter(is_blocked=False)
    elif status == 'blocked':
        qs = qs.filter(is_blocked=True)

    total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
    active_count    = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=False).count()
    blocked_count   = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=True).count()

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


def customer_detail(request, pk):
    customer = get_object_or_404(
        User.objects.annotate(order_count=Count('orders')),
        pk=pk, is_staff=False, is_superuser=False
    )
    orders = customer.orders.order_by('-created_at')
    total_spent = orders.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or 0
    context = {
        'customer':    customer,
        'orders':      orders,
        'total_spent': total_spent,
    }
    return render(request, 'custom_admin/customers/customer_detail.html', context)


def customer_block_toggle(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False, is_superuser=False)
    if request.method == 'POST':
        customer.is_blocked = not customer.is_blocked
        customer.save(update_fields=['is_blocked'])
        action = 'blocked' if customer.is_blocked else 'unblocked'
        messages.success(request, f'Customer "{customer.username}" has been {action}.')
    return redirect('custom_admin:customer_detail', pk=pk)