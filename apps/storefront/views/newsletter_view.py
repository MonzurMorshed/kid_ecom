import re
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from kidurabd.email_service import send_templated_email
from ..models import NewsletterSubscriber

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


@require_POST
def newsletter_subscribe(request):
    """
    Subscribes an email to the newsletter and sends a welcome email via care@kidurabd.com.
    Supports both AJAX and standard form submissions.
    """
    email = request.POST.get('email', '').strip().lower()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not email or not EMAIL_REGEX.match(email):
        err_msg = 'Please provide a valid email address.'
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect(request.META.get('HTTP_REFERER', 'storefront:index'))

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True},
    )

    if not created and subscriber.is_active:
        msg = "You're already on our list! Thank you for staying connected. 🎉"
        if is_ajax:
            return JsonResponse({'status': 'info', 'message': msg})
        messages.info(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'storefront:index'))

    if not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=['is_active'])

    # Send welcome email from care@kidurabd.com
    site_name = getattr(settings, 'SITE_NAME', 'Kidurabd')
    send_templated_email(
        channel='care',
        subject=f'Welcome to the {site_name} Family! 🎈',
        template_name='emails/newsletter_welcome.html',
        context={'email': email},
        to=email,
        reply_to=['care@kidurabd.com'],
        fail_silently=True,
    )

    welcome_msg = "You're on the list — welcome to the playful side 🎉"
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': welcome_msg})

    messages.success(request, welcome_msg)
    return redirect(request.META.get('HTTP_REFERER', 'storefront:index'))
