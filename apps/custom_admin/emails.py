"""
Email notification helpers for the custom_admin module.
"""

from __future__ import annotations

import logging
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from custom_admin.models import SiteSettings, AdminProfile
from kidurabd.email_service import send_templated_email

logger = logging.getLogger('kidurabd.emails')


def get_superadmin_notification_emails() -> list[str]:
    """
    Collect email addresses of all Super Admins, superusers, and configured store email.
    """
    recipients = set()

    # 1. Django superusers
    for email in User.objects.filter(is_superuser=True, is_active=True).exclude(email='').values_list('email', flat=True):
        if email and '@' in email:
            recipients.add(email.strip())

    # 2. Staff users with 'superadmin' role in AdminProfile
    for email in User.objects.filter(admin_profile__role='superadmin', is_active=True).exclude(email='').values_list('email', flat=True):
        if email and '@' in email:
            recipients.add(email.strip())

    # 3. Store notification email from SiteSettings
    try:
        site_settings = SiteSettings.get_settings()
        if site_settings.site_email and '@' in site_settings.site_email:
            recipients.add(site_settings.site_email.strip())
    except Exception as e:
        logger.warning(f"Could not load SiteSettings for admin email alert: {e}")

    # 4. Fallback setting or default mailbox
    configured_fallback = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
    if configured_fallback and '@' in configured_fallback:
        recipients.add(configured_fallback.strip())

    if not recipients:
        recipients.add(getattr(settings, 'EMAIL_HOST_USER', 'notification@kidurabd.com'))

    return list(recipients)


def send_new_staff_registration_alert(staff_user: User, request=None) -> bool:
    """
    Send an email alert to Super Admins when a new staff user registers via the admin sign-up form.
    The new staff account is created inactive by default and requires Super Admin review & activation.
    """
    site_settings = SiteSettings.get_settings()
    site_name = site_settings.site_name or 'Kidurabd'

    if request:
        try:
            review_url = request.build_absolute_uri(reverse('custom_admin:admin_user_edit', args=[staff_user.pk]))
        except Exception:
            review_url = f"/admin/admin-users/{staff_user.pk}/edit/"

        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip_address = x_forwarded.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    else:
        review_url = f"/admin/admin-users/{staff_user.pk}/edit/"
        ip_address = None

    recipients = get_superadmin_notification_emails()
    if not recipients:
        return False

    context = {
        'site_name': site_name,
        'staff_user': staff_user,
        'registered_at': timezone.now(),
        'review_url': review_url,
        'ip_address': ip_address,
    }

    subject = f'[{site_name}] 👤 New Staff Registration: {staff_user.username} (Pending Approval)'

    logger.info(f"Sending new staff registration notification for {staff_user.username} to {recipients}")
    return send_templated_email(
        channel='notification',
        subject=subject,
        template_name='emails/admin_new_staff_notification.html',
        context=context,
        to=recipients,
        fail_silently=True,
    )


def send_staff_activation_notification(staff_user: User, request=None) -> bool:
    """
    Send an email notification to the staff user once their account has been activated.
    """
    if not staff_user.email or '@' not in staff_user.email:
        return False

    site_settings = SiteSettings.get_settings()
    site_name = site_settings.site_name or 'Kidurabd'

    try:
        profile = staff_user.admin_profile
        role_name = profile.get_role_display()
    except Exception:
        role_name = 'Staff'

    if request:
        try:
            login_url = request.build_absolute_uri(reverse('custom_admin:login'))
        except Exception:
            login_url = "/admin/login/"
    else:
        login_url = "/admin/login/"

    context = {
        'site_name': site_name,
        'staff_user': staff_user,
        'role_name': role_name,
        'login_url': login_url,
    }

    subject = f'[{site_name}] 🎉 Your Staff Account has been Activated'

    logger.info(f"Sending staff activation confirmation to {staff_user.email}")
    return send_templated_email(
        channel='notification',
        subject=subject,
        template_name='emails/staff_account_activated.html',
        context=context,
        to=staff_user.email,
        fail_silently=True,
    )
