"""
Transactional email helpers for the orders and customer app.

Uses the 'billing' channel for orders, invoices, and status updates.
Uses the 'care' channel for welcome emails.
"""

from __future__ import annotations

from django.conf import settings
from kidurabd.email_service import send_templated_email

SITE_NAME = getattr(settings, 'SITE_NAME', 'Kidurabd')
ADMIN_EMAIL = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'notification@kidurabd.com')


# ── Order placed — confirmation to customer ───────────────────────────────────

def send_order_placed(order) -> bool:
    """Send an order-confirmation email to the customer right after checkout via billing@kidurabd.com."""
    ctx = {
        'order': order,
        'items': order.items.select_related('product', 'variant').all(),
    }
    return send_templated_email(
        channel='billing',
        subject=f'[{SITE_NAME}] Order #{order.id:05d} Confirmed 🎉',
        template_name='emails/order_placed.html',
        context=ctx,
        to=order.email,
        reply_to=['billing@kidurabd.com'],
        fail_silently=True,
    )


# ── Order status update — to customer ─────────────────────────────────────────

STATUS_LABELS = {
    'PENDING':    ('⏳', 'Pending',    'Your order is pending review.'),
    'CONFIRMED':  ('✅', 'Confirmed',  'Your order has been confirmed and will be dispatched soon.'),
    'PROCESSING': ('📦', 'Processing', 'Your order is being prepared and packed.'),
    'DELIVERED':  ('🎉', 'Delivered',  'Your order has been delivered. We hope you love it!'),
    'CANCELLED':  ('❌', 'Cancelled',  'Your order has been cancelled. Contact us if this is a mistake.'),
}

def send_order_status_update(order) -> bool:
    """Notify the customer whenever an admin changes the order status via billing@kidurabd.com."""
    emoji, label, detail = STATUS_LABELS.get(order.status, ('📋', order.status, ''))
    ctx = {
        'order':         order,
        'status_emoji':  emoji,
        'status_label':  label,
        'status_detail': detail,
    }
    return send_templated_email(
        channel='billing',
        subject=f'[{SITE_NAME}] Order #{order.id:05d} — {label} {emoji}',
        template_name='emails/order_status_update.html',
        context=ctx,
        to=order.email,
        reply_to=['billing@kidurabd.com'],
        fail_silently=True,
    )


# ── New order — admin notification ────────────────────────────────────────────

def send_admin_new_order(order) -> bool:
    """Notify the store admin when a new order is placed."""
    ctx = {
        'order': order,
        'items': order.items.select_related('product', 'variant').all(),
    }
    return send_templated_email(
        channel='billing',
        subject=f'[{SITE_NAME}] 🛍️ New Order #{order.id:05d} from {order.full_name}',
        template_name='emails/admin_new_order.html',
        context=ctx,
        to=ADMIN_EMAIL,
        fail_silently=True,
    )


# ── Welcome email — on registration ───────────────────────────────────────────

def send_welcome_email(user) -> bool:
    """Send a welcome email to a newly registered customer via care@kidurabd.com."""
    ctx = {
        'user': user,
    }
    return send_templated_email(
        channel='care',
        subject=f'Welcome to {SITE_NAME}! 🎉',
        template_name='emails/welcome.html',
        context=ctx,
        to=user.email,
        reply_to=['care@kidurabd.com'],
        fail_silently=True,
    )
