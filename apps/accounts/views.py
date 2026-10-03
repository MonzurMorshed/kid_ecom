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
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from functools import wraps

from .models import User, Wishlist, UserAddress
from .forms import (
    CustomerRegisterForm, CustomerLoginForm, CustomerProfileForm,
    CustomerChangePasswordForm, CustomerForgotPasswordForm, CustomerResetPasswordForm,
    UserAddressForm,
)
from orders.models import Order
from products.models import Product, ProductReview


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
            # Merge any guest-session cart items into the user's DB cart
            if not user.is_staff and not user.is_superuser:
                from apps.storefront.cart import merge_session_cart_to_user
                merge_session_cart_to_user(request, user)
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
    orders = user.orders.filter(is_deleted=False).order_by('-created_at')[:5]
    total_spent = user.orders.filter(status='DELIVERED').aggregate(t=Sum('total_amount'))['t'] or 0
    wishlist_count = Wishlist.objects.filter(user=user).count()
    addresses = user.addresses.all()
    default_address = addresses.filter(is_default=True).first() or addresses.first()
    return render(request, 'accounts/profile.html', {
        'customer': user,
        'recent_orders': orders,
        'total_spent': total_spent,
        'wishlist_count': wishlist_count,
        'addresses_count': addresses.count(),
        'default_address': default_address,
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


# ──────────────────────────────────────────────────────────────────────────────
# Order Detail / Tracking  (accounts:order_detail)
# ──────────────────────────────────────────────────────────────────────────────

@customer_required
def order_detail(request, pk):
    """Dedicated order tracking page for the logged-in customer."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product__images', 'items__variant'),
        pk=pk,
        user=request.user,
        is_deleted=False,
    )
    return render(request, 'accounts/order_detail.html', {'order': order})


# ──────────────────────────────────────────────────────────────────────────────
# Wishlist Page  (accounts:wishlist)
# ──────────────────────────────────────────────────────────────────────────────

@customer_required
def wishlist_page(request):
    """Display all products in the customer's server-side wishlist."""
    items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related('product__category')
        .prefetch_related('product__images')
    )
    # IDs set used in template to mark heart as filled
    wishlist_ids = set(items.values_list('product_id', flat=True))
    return render(request, 'accounts/wishlist.html', {
        'wishlist_items': items,
        'wishlist_ids': wishlist_ids,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Wishlist Toggle  (accounts:wishlist_toggle)  — AJAX POST
# ──────────────────────────────────────────────────────────────────────────────

@require_POST
def wishlist_toggle(request):
    """
    Toggle a product in/out of the authenticated customer's wishlist.
    Returns JSON: {wishlisted: bool, count: int}
    If the user is not authenticated, redirects or returns 401 for AJAX.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not request.user.is_authenticated or request.user.is_staff or request.user.is_superuser:
        if is_ajax:
            return JsonResponse({'error': 'login_required'}, status=401)
        messages.info(request, 'Please log in to save items to your wishlist.')
        return redirect('accounts:login')

    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, pk=product_id, is_active=True, is_deleted=False)

    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        wishlisted = False
    else:
        wishlisted = True

    count = Wishlist.objects.filter(user=request.user).count()

    if is_ajax:
        return JsonResponse({'wishlisted': wishlisted, 'count': count})

    if wishlisted:
        messages.success(request, f'"{product.title}" added to your wishlist.')
    else:
        messages.info(request, f'"{product.title}" removed from your wishlist.')
    return redirect(request.POST.get('next') or 'accounts:wishlist')


# ──────────────────────────────────────────────────────────────────────────────
# Review History  (accounts:review_history)
# ──────────────────────────────────────────────────────────────────────────────

@customer_required
def review_history(request):
    """Show all product reviews submitted by the logged-in customer."""
    reviews = (
        ProductReview.objects
        .filter(user=request.user)
        .select_related('product')
        .prefetch_related('product__images')
        .order_by('-created_at')
    )
    paginator = Paginator(reviews, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'accounts/review_history.html', {
        'page_obj': page_obj,
        'reviews_count': reviews.count(),
    })


# ──────────────────────────────────────────────────────────────────────────────
# Address Book (accounts:address_list, address_create, address_edit, etc.)
# ──────────────────────────────────────────────────────────────────────────────

@customer_required
def address_list(request):
    """Show customer's saved address book."""
    addresses = request.user.addresses.all()
    return render(request, 'accounts/address_list.html', {
        'addresses': addresses,
        'addresses_count': addresses.count(),
    })


@customer_required
def address_create(request):
    """Create a new saved shipping address."""
    if request.method == 'POST':
        form = UserAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if not request.user.addresses.exists():
                address.is_default = True
            address.save()
            messages.success(request, 'Address saved successfully! 🏡')
            return redirect('accounts:address_list')
    else:
        initial = {
            'full_name': request.user.get_full_name() or request.user.first_name or '',
            'phone_number': request.user.phone_number or '',
            'country': 'Bangladesh',
            'is_default': not request.user.addresses.exists(),
        }
        form = UserAddressForm(initial=initial)

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'action_title': 'Add New Address',
        'is_edit': False,
    })


@customer_required
def address_edit(request, pk):
    """Edit an existing saved address."""
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully! ✨')
            return redirect('accounts:address_list')
    else:
        form = UserAddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'address': address,
        'action_title': 'Edit Address',
        'is_edit': True,
    })


@customer_required
@require_POST
def address_delete(request, pk):
    """Delete a saved address."""
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    was_default = address.is_default
    address.delete()

    if was_default:
        next_default = request.user.addresses.first()
        if next_default:
            next_default.is_default = True
            next_default.save()

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '')
    )
    if is_ajax:
        return JsonResponse({'success': True, 'message': 'Address deleted successfully.'})

    messages.success(request, 'Address removed from your address book.')
    return redirect('accounts:address_list')


@customer_required
@require_POST
def address_set_default(request, pk):
    """Set an address as default."""
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    address.is_default = True
    address.save()

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '')
    )
    if is_ajax:
        return JsonResponse({'success': True, 'message': 'Default address updated.'})

    messages.success(request, f'Default shipping address updated to "{address.address_line1}".')
    return redirect('accounts:address_list')