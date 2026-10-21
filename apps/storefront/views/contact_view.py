import logging
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from custom_admin.models import SiteSettings
from kidurabd.email_service import send_templated_email
from ..forms import ContactForm

logger = logging.getLogger(__name__)


def contact_view(request):
    """
    Renders the Contact Us page and processes customer inquiry submissions.
    Emails the inquiry to contact@kidurabd.com and sends an auto-acknowledgment
    to the customer via the dedicated contact email channel.
    """
    site_settings = SiteSettings.get_settings()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # 1. Alert Store / Contact Mailbox
            contact_mailbox = getattr(settings, 'CONTACT_EMAIL_USER', 'contact@kidurabd.com')
            send_templated_email(
                channel='contact',
                subject=f'[{site_settings.site_name}] New Inquiry: {contact.subject}',
                template_name='emails/contact_admin_alert.html',
                context={
                    'contact': contact,
                    'site_name': site_settings.site_name,
                },
                to=contact_mailbox,
                reply_to=[contact.email],
                fail_silently=True,
            )

            # 2. Acknowledgment to Customer
            send_templated_email(
                channel='contact',
                subject=f'We received your message! — {site_settings.site_name}',
                template_name='emails/contact_acknowledgment.html',
                context={
                    'contact': contact,
                    'site_name': site_settings.site_name,
                },
                to=contact.email,
                reply_to=[contact_mailbox],
                fail_silently=True,
            )

            success_msg = 'Thank you! Your message has been sent. We will get back to you shortly.'

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': success_msg})

            messages.success(request, success_msg)
            return redirect('storefront:contact')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        # Prepopulate email/name if customer is logged in
        initial = {}
        if request.user.is_authenticated:
            initial['name'] = request.user.get_full_name() or request.user.first_name
            initial['email'] = request.user.email
            if hasattr(request.user, 'phone'):
                initial['phone'] = getattr(request.user, 'phone', '')
        form = ContactForm(initial=initial)

    return render(request, 'storefront/contact.html', {
        'form': form,
        'site_settings': site_settings,
    })
