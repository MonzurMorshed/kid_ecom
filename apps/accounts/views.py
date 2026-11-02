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

from .models import User, Wishlist, UserAddress, OTPCode
from .forms import (
    CustomerRegisterForm, CustomerLoginForm, CustomerProfileForm,
    CustomerChangePasswordForm, CustomerForgotPasswordForm, CustomerResetPasswordForm,
    UserAddressForm, OTPVerifyForm,
)
from kidurabd.sms_service import send_sms
from orders.models import Order
from products.models import Product, ProductReview


def _mask_phone(phone: str) -> str:
    """Mask phone for display, e.g. 01712345678 -> 017****5678"""
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone


# ── Auth decorators ───────────────────────────────────────────────────────────

def customer_required(view_func):
    """Redirect to login if not authenticated."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, 'Please log in to access that page.')
            return redirect('accounts:login')
        if request.user.is_blocked:
            logout(request)
            messages.error(request, 'Your account has been suspended. Please contact support.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def guest_only(view_func):
    """Redirect logged-in customers to their profile, but allow admins to access customer login/register."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_staff and not request.user.is_superuser:
                return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ──────────────────────────────────────────────────────────────────────────────
# Register (Step 1: Details -> OTP)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def register_view(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            # Store signup payload in session pending OTP verification
            request.session['signup_data'] = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data.get('last_name', ''),
                'phone_number': form.cleaned_data['phone_number'],
                'email': form.cleaned_data.get('email', ''),
                'password': form.cleaned_data['password'],
            }
            # Generate and send OTP via SMS
            otp = OTPCode.generate_for(form.cleaned_data['phone_number'], 'signup')
            site_name = getattr(settings, 'SITE_NAME', 'Kidurabd')
            send_sms(
                form.cleaned_data['phone_number'],
                f"[{site_name}] Your verification OTP code is {otp.code}. Valid for 10 minutes."
            )
            messages.info(request, f"We have sent a 6-digit OTP to {_mask_phone(form.cleaned_data['phone_number'])}. Please enter it below.")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                request.session['signup_next'] = next_url
            return redirect('accounts:verify_signup_otp')
    else:
        form = CustomerRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Verify Signup OTP (Step 2: OTP -> Account Creation)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def verify_signup_otp_view(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        messages.warning(request, 'Please fill in the registration form first.')
        return redirect('accounts:register')

    phone = signup_data['phone_number']
    site_name = getattr(settings, 'SITE_NAME', 'Kidurabd')

    # Handle resend OTP request
    if request.method == 'POST' and request.POST.get('action') == 'resend':
        otp = OTPCode.generate_for(phone, 'signup')
        send_sms(phone, f"[{site_name}] Your verification OTP code is {otp.code}. Valid for 10 minutes.")
        messages.success(request, f'A new OTP code has been sent to {_mask_phone(phone)}.')
        return redirect('accounts:verify_signup_otp')

    form = OTPVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        otp = OTPCode.verify(phone, code, 'signup')
        if not otp:
            form.add_error('code', 'Invalid or expired OTP code. Please try again or request a new code.')
        else:
            otp.consume()

            # Ensure phone is unique in DB before creating
            if User.objects.filter(phone_number=phone).exists():
                messages.error(request, 'An account with this mobile number already exists. Please log in.')
                request.session.pop('signup_data', None)
                return redirect('accounts:login')

            user = User.objects.create_user(
                username=phone,
                phone_number=phone,
                email=signup_data.get('email', ''),
                first_name=signup_data['first_name'],
                last_name=signup_data.get('last_name', ''),
                is_customer=True,
                password=signup_data['password'],
            )

            # Clean up session
            request.session.pop('signup_data', None)
            next_url = request.session.pop('signup_next', None)

            # Auto log in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Send welcome email if customer provided an email address
            if user.email:
                from orders.emails import send_welcome_email
                send_welcome_email(user)

            messages.success(request, f'Welcome to {site_name}, {user.first_name}! 🎉 Your account is verified.')
            return redirect(next_url or 'storefront:index')

    return render(request, 'accounts/otp_verify.html', {
        'form': form,
        'phone_masked': _mask_phone(phone),
        'purpose': 'signup',
        'title': 'Verify Your Mobile Number',
        'subtitle': f'Enter the 6-digit verification code sent to {_mask_phone(phone)}',
        'resend_url': request.path,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Login (by Mobile Number)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def login_view(request):
    form = CustomerLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        phone = form.cleaned_data['phone_number']
        password = form.cleaned_data['password']
        remember = form.cleaned_data.get('remember_me', False)

        # Lookup customer by phone_number, or by username
        u = User.objects.filter(phone_number=phone).first()
        if not u:
            # Fallback for any legacy users where username matches the phone
            u = User.objects.filter(username__iexact=phone).first()

        auth_username = u.username if u else phone
        user = authenticate(request, username=auth_username, password=password)

        if user is not None:
            if user.is_blocked:
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return redirect('accounts:login')
            login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Session cookie expires when browser closes
            else:
                request.session.set_expiry(getattr(settings, 'SESSION_COOKIE_AGE', 86400))  # 1 day (24 hours)

            # Merge any guest-session cart items into the user's DB cart
            from storefront.cart import merge_session_cart_to_user
            merge_session_cart_to_user(request, user)

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'storefront:index')
        else:
            messages.error(request, 'No account found with that mobile number and password.')

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
# Forgot Password (Step 1: Phone -> Send OTP)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def forgot_password_view(request):
    if request.method == 'POST':
        form = CustomerForgotPasswordForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            user = User.objects.filter(phone_number=phone, is_staff=False, is_superuser=False).first()
            if not user:
                # Also check username in case username is the phone
                user = User.objects.filter(username=phone, is_staff=False, is_superuser=False).first()

            if user and user.phone_number:
                otp = OTPCode.generate_for(user.phone_number, 'reset')
                site_name = getattr(settings, 'SITE_NAME', 'Kidurabd')
                send_sms(
                    user.phone_number,
                    f"[{site_name}] Your password reset OTP is {otp.code}. Valid for 10 minutes."
                )
                request.session['reset_phone'] = user.phone_number
                messages.info(request, f"A 6-digit reset OTP has been sent to {_mask_phone(user.phone_number)}.")
                return redirect('accounts:verify_reset_otp')
            else:
                messages.error(request, 'No customer account found with that mobile number.')
                return redirect('accounts:forgot_password')
    else:
        form = CustomerForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Verify Reset OTP (Step 2: Enter OTP)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def verify_reset_otp_view(request):
    phone = request.session.get('reset_phone')
    if not phone:
        messages.warning(request, 'Please enter your mobile number first.')
        return redirect('accounts:forgot_password')

    site_name = getattr(settings, 'SITE_NAME', 'Kidurabd')

    if request.method == 'POST' and request.POST.get('action') == 'resend':
        otp = OTPCode.generate_for(phone, 'reset')
        send_sms(phone, f"[{site_name}] Your password reset OTP is {otp.code}. Valid for 10 minutes.")
        messages.success(request, f'A new reset OTP has been sent to {_mask_phone(phone)}.')
        return redirect('accounts:verify_reset_otp')

    form = OTPVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        otp = OTPCode.verify(phone, code, 'reset')
        if not otp:
            form.add_error('code', 'Invalid or expired OTP code. Please try again or request a new code.')
        else:
            otp.consume()
            request.session['reset_verified_phone'] = phone
            return redirect('accounts:reset_password_phone')

    return render(request, 'accounts/otp_verify.html', {
        'form': form,
        'phone_masked': _mask_phone(phone),
        'purpose': 'reset',
        'title': 'Verify Reset Code',
        'subtitle': f'Enter the 6-digit verification code sent to {_mask_phone(phone)}',
        'resend_url': request.path,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Reset Password with Phone (Step 3: New Password)
# ──────────────────────────────────────────────────────────────────────────────
@guest_only
def reset_password_phone_view(request):
    phone = request.session.get('reset_verified_phone')
    if not phone:
        messages.warning(request, 'Please verify your mobile number first.')
        return redirect('accounts:forgot_password')

    user = User.objects.filter(phone_number=phone).first()
    if not user:
        user = User.objects.filter(username=phone).first()

    if not user:
        request.session.pop('reset_verified_phone', None)
        messages.error(request, 'Account not found.')
        return redirect('accounts:login')

    if request.method == 'POST':
        form = CustomerResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            request.session.pop('reset_phone', None)
            request.session.pop('reset_verified_phone', None)
            messages.success(request, 'Your password has been reset successfully! Please log in with your new password.')
            return redirect('accounts:login')
    else:
        form = CustomerResetPasswordForm()

    return render(request, 'accounts/reset_password_phone.html', {
        'form': form,
        'phone_masked': _mask_phone(phone),
    })


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
    Returns JSON: {wishlisted: bool, count: int, success: bool}
    If the user is not authenticated, redirects or returns 401 for AJAX.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json'

    if not request.user.is_authenticated:
        login_url = '/accounts/login/?next=' + (request.POST.get('next') or request.META.get('HTTP_REFERER') or '/')
        if is_ajax:
            return JsonResponse({'error': 'login_required', 'login_url': login_url}, status=401)
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
        return JsonResponse({
            'success': True,
            'wishlisted': wishlisted,
            'count': count,
            'message': f'"{product.title}" added to your wishlist.' if wishlisted else f'"{product.title}" removed from your wishlist.'
        })

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