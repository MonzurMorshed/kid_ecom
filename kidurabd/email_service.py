"""
Multi-channel transactional email service for Kidurabd.

Supports sending from dedicated domain mailboxes:
  • 'notification' : notification@kidurabd.com (Password resets, security alerts)
  • 'billing'      : billing@kidurabd.com      (Order placed, invoices, status updates)
  • 'contact'      : contact@kidurabd.com      (Contact form submissions & acknowledgments)
  • 'care'         : care@kidurabd.com         (Customer support, newsletter welcome)

All emails are sent as multipart/alternative (HTML + clean plain-text fallback)
and are wrapped with fail-safe error handling so mail delivery glitches
never break user checkout or authentication workflows.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('kidurabd.emails')


def _get_channel_config(channel: str = 'notification') -> dict[str, Any]:
    """Resolve SMTP credentials and from_email for a specific mailbox channel."""
    channel = (channel or 'notification').lower()

    if channel == 'billing':
        user = getattr(settings, 'BILLING_EMAIL_USER', 'billing@kidurabd.com')
        pwd  = getattr(settings, 'BILLING_EMAIL_PASSWORD', '')
        from_email = getattr(settings, 'BILLING_FROM_EMAIL', f'Kidurabd Billing <{user}>')
    elif channel == 'contact':
        user = getattr(settings, 'CONTACT_EMAIL_USER', 'contact@kidurabd.com')
        pwd  = getattr(settings, 'CONTACT_EMAIL_PASSWORD', '')
        from_email = getattr(settings, 'CONTACT_FROM_EMAIL', f'Kidurabd Contact <{user}>')
    elif channel == 'care':
        user = getattr(settings, 'CARE_EMAIL_USER', 'care@kidurabd.com')
        pwd  = getattr(settings, 'CARE_EMAIL_PASSWORD', '')
        from_email = getattr(settings, 'CARE_FROM_EMAIL', f'Kidurabd Care <{user}>')
    else:  # notification / default
        user = getattr(settings, 'EMAIL_HOST_USER', 'notification@kidurabd.com')
        pwd  = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', f'Kidurabd <{user}>')

    return {
        'channel': channel,
        'user': user,
        'password': pwd,
        'from_email': from_email,
    }


def get_channel_connection(channel: str = 'notification'):
    """
    Return a Django mail connection for the specified channel.
    If EMAIL_BACKEND is SMTP and credentials exist, builds an authenticated SMTP backend.
    Otherwise falls back to Django's configured default backend (e.g. console).
    """
    cfg = _get_channel_config(channel)
    backend_path = getattr(settings, 'EMAIL_BACKEND', '')

    if 'smtp' in backend_path.lower() and cfg['user'] and cfg['password']:
        return EmailBackend(
            host=getattr(settings, 'EMAIL_HOST', 'premium365-2.web-hosting.com'),
            port=getattr(settings, 'EMAIL_PORT', 465),
            username=cfg['user'],
            password=cfg['password'],
            use_ssl=getattr(settings, 'EMAIL_USE_SSL', True),
            use_tls=getattr(settings, 'EMAIL_USE_TLS', False),
            timeout=getattr(settings, 'EMAIL_TIMEOUT', 10),
        )

    # In development / console backend or tests
    return get_connection()


def send_templated_email(
    channel: str,
    subject: str,
    template_name: str,
    context: dict[str, Any],
    to: str | Sequence[str],
    *,
    reply_to: Sequence[str] | None = None,
    fail_silently: bool = True,
) -> bool:
    """
    Render and send an HTML + plain-text email through the requested mailbox channel.

    Args:
        channel: 'notification', 'billing', 'contact', or 'care'
        subject: Email subject line
        template_name: Template path (e.g. 'emails/password_reset.html')
        context: Context dict passed to the template
        to: Recipient email address or list of addresses
        reply_to: Optional list of reply-to addresses
        fail_silently: When True, catches exceptions and returns False
    """
    cfg = _get_channel_config(channel)
    to_list = [to] if isinstance(to, str) else list(to)

    # Standard context items
    merged_context = {
        'site_name': getattr(settings, 'SITE_NAME', 'Kidurabd'),
        'site_url': getattr(settings, 'SITE_URL', 'https://kidurabd.com'),
        'support_email': getattr(settings, 'CARE_EMAIL_USER', 'care@kidurabd.com'),
        'billing_email': getattr(settings, 'BILLING_EMAIL_USER', 'billing@kidurabd.com'),
        'contact_email': getattr(settings, 'CONTACT_EMAIL_USER', 'contact@kidurabd.com'),
    }
    merged_context.update(context)

    try:
        html_content = render_to_string(template_name, merged_context)
        import re
        # Strip <style> and <script> blocks so CSS/JS doesn't leak into plain-text email
        clean_html = re.sub(r'<(style|script)[^>]*>[\s\S]*?</\1>', '', html_content, flags=re.IGNORECASE)
        text_content = re.sub(r'\n\s*\n', '\n\n', strip_tags(clean_html)).strip()

        connection = get_channel_connection(channel)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=cfg['from_email'],
            to=to_list,
            reply_to=list(reply_to) if reply_to else None,
            connection=connection,
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f"Email sent [{channel}] '{subject}' -> {to_list}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email [{channel}] '{subject}' -> {to_list}: {exc}")
        if not fail_silently:
            raise
        return False
