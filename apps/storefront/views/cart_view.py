import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product, ProductVariant
from orders.models import Order, OrderItem
from ..cart import Cart


# ── helpers ───────────────────────────────────────────────────────────────────

def _json_cart(cart):
    return JsonResponse(cart.as_dict())


# ── Cart page ─────────────────────────────────────────────────────────────────

def cart_page(request):
    cart = Cart(request)
    return render(request, 'storefront/cart.html', {'cart': cart})


# ── Add to cart (AJAX + normal POST) ─────────────────────────────────────────

@require_POST
def cart_add(request):
    cart = Cart(request)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id') or None
    qty        = int(request.POST.get('qty', 1))

    product = get_object_or_404(Product, pk=product_id, is_active=True, is_deleted=False)
    variant = get_object_or_404(ProductVariant, pk=variant_id, product=product) if variant_id else None

    cart.add(product, qty=qty, variant=variant)

    if is_ajax:
        return _json_cart(cart)

    messages.success(request, f'"{product.title}" added to your bag!')
    return redirect(request.POST.get('next') or 'storefront:cart')


# ── Remove from cart ──────────────────────────────────────────────────────────

@require_POST
def cart_remove(request):
    cart = Cart(request)
    key = request.POST.get('key', '')
    if not key and request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            key = payload.get('key', '')
        except Exception:
            pass

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    cart.remove(key)

    if is_ajax:
        return _json_cart(cart)
    return redirect('storefront:cart')


# ── Update quantity ───────────────────────────────────────────────────────────

@require_POST
def cart_update(request):
    cart = Cart(request)
    key = request.POST.get('key', '')
    qty = request.POST.get('qty', 1)
    if not key and request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            key = payload.get('key', '')
            qty = payload.get('qty', 1)
        except Exception:
            pass

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    cart.update_qty(key, qty)

    if is_ajax:
        return _json_cart(cart)
    return redirect('storefront:cart')


# ── Cart count (AJAX) ─────────────────────────────────────────────────────────

def cart_count(request):
    cart = Cart(request)
    return JsonResponse({'count': cart.item_count, 'total': str(cart.total)})


# ── Checkout ──────────────────────────────────────────────────────────────────

def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.info(request, 'Your bag is empty.')
        return redirect('storefront:cart')

    # Pre-fill from logged-in user if available
    user = request.user if request.user.is_authenticated else None
    initial = {}
    if user and not user.is_staff:
        default_addr = user.addresses.filter(is_default=True).first() or user.addresses.first()
        initial = {
            'full_name':        default_addr.full_name if default_addr else (user.get_full_name() or user.username),
            'email':            user.email,
            'phone_number':     default_addr.phone_number if default_addr else (user.phone_number or ''),
            'shipping_address': default_addr.formatted if default_addr else (user.address or ''),
        }

    if request.method == 'POST':
        full_name        = request.POST.get('full_name', '').strip()
        email            = request.POST.get('email', '').strip()
        phone_number     = request.POST.get('phone_number', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()

        errors = {}
        if not full_name:        errors['full_name']        = 'Full name is required.'
        if not email:            errors['email']            = 'Email is required.'
        if not phone_number:     errors['phone_number']     = 'Phone number is required.'
        if not shipping_address: errors['shipping_address'] = 'Delivery address is required.'

        if not errors:
            is_new_user = False
            auto_password = None

            if request.user.is_authenticated:
                order_user = request.user
            else:
                from accounts.models import User as UserModel
                order_user = UserModel.objects.filter(email__iexact=email).first()
                if not order_user:
                    is_new_user = True
                    import secrets
                    import re

                    parts = full_name.strip().split(maxsplit=1)
                    first_name = parts[0] if parts else 'Customer'
                    last_name = parts[1] if len(parts) > 1 else ''

                    # Generate clean, unique username based on email prefix
                    clean_prefix = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0].lower())
                    if not clean_prefix or len(clean_prefix) < 3:
                        clean_prefix = 'user'

                    base_username = clean_prefix
                    username = base_username
                    while UserModel.objects.filter(username__iexact=username).exists():
                        username = f"{base_username}_{secrets.randbelow(9000) + 1000}"

                    # Generate clean, user-friendly temporary password (10 chars, letters & digits)
                    alphabet = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
                    auto_password = ''.join(secrets.choice(alphabet) for _ in range(10))

                    # Safely handle phone number uniqueness
                    user_phone = phone_number
                    if UserModel.objects.filter(phone_number=phone_number).exists():
                        user_phone = None

                    order_user = UserModel.objects.create_user(
                        username=username,
                        email=email.lower(),
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=user_phone,
                        is_customer=True,
                        password=auto_password,
                    )

                    # Save address to address book
                    try:
                        from accounts.models import UserAddress
                        UserAddress.objects.create(
                            user=order_user,
                            full_name=full_name,
                            phone_number=phone_number,
                            address_line1=shipping_address,
                            city='Dhaka',
                            is_default=True,
                        )
                    except Exception:
                        pass

                    # Automatically log in the newly registered user
                    from django.contrib.auth import login
                    login(request, order_user, backend='django.contrib.auth.backends.ModelBackend')

            order = Order.objects.create(
                user=order_user,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                shipping_address=shipping_address,
                total_amount=cart.grand_total,
                status='PENDING',
            )

            for item in cart:
                product = get_object_or_404(Product, pk=item['product_id'])
                variant = None
                if item.get('variant_id'):
                    variant = ProductVariant.objects.filter(pk=item['variant_id']).first()

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    quantity=item['qty'],
                    price=Decimal(item['price']),
                )

            cart.clear()

            # ── Transactional emails ──────────────────────────────────────────
            from orders.emails import send_order_placed, send_admin_new_order, send_auto_registration_email

            if is_new_user and auto_password:
                send_auto_registration_email(order_user, auto_password, order=order)
                request.session['just_auto_registered'] = {
                    'username': order_user.username,
                    'email': order_user.email,
                }

            send_order_placed(order)
            send_admin_new_order(order)

            messages.success(request, f'🎉 Order #{order.id} placed! Thank you, {full_name}.')
            return redirect('storefront:order_success', pk=order.pk)

        return render(request, 'storefront/checkout.html', {
            'cart':      cart,
            'errors':    errors,
            'form_data': request.POST,
            'values':    request.POST,
            'initial':   initial,
        })

    return render(request, 'storefront/checkout.html', {
        'cart':      cart,
        'errors':    {},
        'form_data': initial,
        'values':    initial,
        'initial':   initial,
    })


# ── Order success ─────────────────────────────────────────────────────────────

def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk)
    just_registered = request.session.pop('just_auto_registered', None)
    return render(request, 'storefront/order_success.html', {
        'order': order,
        'just_registered': just_registered,
    })

