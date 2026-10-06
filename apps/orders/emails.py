"""
Transactional email helpers for the orders app.

All functions accept plain Python objects (no request needed) and are
safe to call with fail_silently=True so a broken mail server never
crashes the user's checkout.

Emails are sent as both plain-text and HTML (multipart/alternative).
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


SITE_NAME     = getattr(settings, 'SITE_NAME',         'Kidurabd')
SITE_URL      = getattr(settings, 'SITE_URL',          'http://127.0.0.1:8000')
FROM_EMAIL    = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kidurabd.com')
ADMIN_EMAIL   = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', FROM_EMAIL)


def _send(subject: str, html: str, to: list[str], *, fail_silently: bool = True):
    """Send a multipart/alternative (HTML + plain-text) email."""
    text = strip_tags(html)
    msg  = EmailMultiAlternatives(subject, text, FROM_EMAIL, to)
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=fail_silently)


# ── Order placed — confirmation to customer ───────────────────────────────────

def send_order_placed(order) -> None:
    """Send an order-confirmation email to the customer right after checkout."""
    ctx = {
        'order':     order,
        'site_name': SITE_NAME,
        'site_url':  SITE_URL,
        'items':     order.items.select_related('product', 'variant').all(),
    }
    html = render_to_string('emails/order_placed.html', ctx)
    _send(
        subject=f'[{SITE_NAME}] Order #{order.id:05d} Confirmed \U0001f389',
        html=html,
        to=[order.email],
    )


# ── Order status update — to customer ─────────────────────────────────────────

STATUS_LABELS = {
    'PENDING':    ('\u23f3', 'Pending',    'Your order is pending review.'),
    'CONFIRMED':  ('\u2705', 'Confirmed',  'Your order has been confirmed and will be dispatched soon.'),
    'PROCESSING': ('\U0001f4e6', 'Processing', 'Your order is being prepared and packed.'),
    'DELIVERED':  ('\U0001f389', 'Delivered',  'Your order has been delivered. We hope you love it!'),
    'CANCELLED':  ('\u274c', 'Cancelled',  'Your order has been cancelled. Contact us if this is a mistake.'),
}

def send_order_status_update(order) -> None:
    """Notify the customer whenever an admin changes the order status."""
    emoji, label, detail = STATUS_LABELS.get(order.status, ('\U0001f4cb', order.status, ''))
    ctx = {
        'order':         order,
        'site_name':     SITE_NAME,
        'site_url':      SITE_URL,
        'status_emoji':  emoji,
        'status_label':  label,
        'status_detail': detail,
    }
    html = render_to_string('emails/order_status_update.html', ctx)
    _send(
        subject=f'[{SITE_NAME}] Order #{order.id:05d} \u2014 {label} {emoji}',
        html=html,
        to=[order.email],
    )


# ── New order — admin notification ────────────────────────────────────────────

def send_admin_new_order(order) -> None:
    """Notify the store admin when a new order is placed."""
    ctx = {
        'order':     order,
        'site_name': SITE_NAME,
        'site_url':  SITE_URL,
        'items':     order.items.select_related('product', 'variant').all(),
    }
    html = render_to_string('emails/admin_new_order.html', ctx)
    _send(
        subject=f'[{SITE_NAME}] \U0001f6cd\ufe0f New Order #{order.id:05d} from {order.full_name}',
        html=html,
        to=[ADMIN_EMAIL],
    )


# ── Welcome email — on registration ───────────────────────────────────────────

def send_welcome_email(user) -> None:
    """Send a welcome email to a newly registered customer."""
    ctx = {
        'user':      user,
        'site_name': SITE_NAME,
        'site_url':  SITE_URL,
    }
    html = render_to_string('emails/welcome.html', ctx)
    _send(
        subject=f'Welcome to {SITE_NAME}! \U0001f389',
        html=html,
        to=[user.email],
    )
