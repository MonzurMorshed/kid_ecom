"""
Generic SMS service for Kidurabd.

Supports multiple SMS backends configured via SiteSettings (DB) or environment variables:
  • 'console'    : Print to console (development / default in DEBUG)
  • 'bulksmsbd'  : BulkSMSBD API (https://bulksmsbd.net/api/smsapi)

Configuration priority:
  1. SiteSettings in DB (custom_admin -> Site Settings -> SMS Gateway)
  2. Environment variables / settings.py (.env fallback)
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger('kidurabd.sms')


def get_sms_settings() -> dict[str, Any]:
    """Retrieve SMS settings dynamically from SiteSettings (DB) with fallback to settings (.env)."""
    try:
        from custom_admin.models import SiteSettings
        site_settings = SiteSettings.get_settings()
        backend = getattr(site_settings, 'sms_backend', None) or getattr(settings, 'SMS_BACKEND', 'console')
        api_key = getattr(site_settings, 'sms_api_key', None) or getattr(settings, 'SMS_API_KEY', '')
        sender_id = getattr(site_settings, 'sms_sender_id', None) or getattr(settings, 'SMS_SENDER_ID', 'Kidurabd')
        manager_phone = getattr(site_settings, 'manager_sms_number', None) or getattr(settings, 'MANAGER_SMS_NUMBER', '')
        return {
            'backend': backend,
            'api_key': api_key,
            'sender_id': sender_id,
            'manager_phone': manager_phone,
            'confirm_customer': getattr(site_settings, 'sms_order_confirm_customer', True),
            'complete_customer': getattr(site_settings, 'sms_order_complete_customer', True),
            'placed_manager': getattr(site_settings, 'sms_order_placed_manager', True),
        }
    except Exception:
        return {
            'backend': getattr(settings, 'SMS_BACKEND', 'console'),
            'api_key': getattr(settings, 'SMS_API_KEY', ''),
            'sender_id': getattr(settings, 'SMS_SENDER_ID', 'Kidurabd'),
            'manager_phone': getattr(settings, 'MANAGER_SMS_NUMBER', ''),
            'confirm_customer': True,
            'complete_customer': True,
            'placed_manager': True,
        }


def send_sms(to: str, message: str) -> bool:
    """
    Send an SMS to the given phone number.

    Args:
        to:      Recipient phone number (e.g. '01712345678')
        message: SMS body text

    Returns:
        True if sent successfully, False on failure (always fail-silently).
    """
    cfg = get_sms_settings()
    backend = cfg.get('backend', 'console')

    try:
        if backend == 'bulksmsbd':
            return _send_bulksmsbd(to, message, cfg=cfg)
        else:
            return _send_console(to, message)
    except Exception as exc:
        logger.error(f"SMS send failed [{backend}] to={to}: {exc}")
        return False


# ── Backend: Console (development) ───────────────────────────────────────────

def _send_console(to: str, message: str) -> bool:
    """Print SMS to console (for local development)."""
    print(f"\n{'='*60}")
    print(f"[SMS Console Backend]")
    print(f"  To     : {to}")
    print(f"  Message: {message}")
    print(f"{'='*60}\n")
    logger.info(f"SMS (console) to={to}: {message[:50]}...")
    return True


# ── Backend: BulkSMSBD ───────────────────────────────────────────────────────

def _send_bulksmsbd(to: str, message: str, cfg: dict[str, Any] | None = None) -> bool:
    """
    Send SMS via BulkSMSBD API.
    POST https://bulksmsbd.net/api/smsapi
    Payload: {api_key, senderid, number, message}
    """
    import urllib.request
    import urllib.parse
    import json

    if cfg is None:
        cfg = get_sms_settings()

    api_key   = cfg.get('api_key') or getattr(settings, 'SMS_API_KEY', '')
    sender_id = cfg.get('sender_id') or getattr(settings, 'SMS_SENDER_ID', 'Kidurabd')

    if not api_key:
        logger.error("SMS_API_KEY is not set in Admin Settings or .env. Cannot send SMS via BulkSMSBD.")
        return False

    url = 'https://bulksmsbd.net/api/smsapi'
    payload = urllib.parse.urlencode({
        'api_key':  api_key,
        'senderid': sender_id,
        'number':   to,
        'message':  message,
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    with urllib.request.urlopen(req, timeout=15) as response:
        raw = response.read().decode('utf-8')
        try:
            data = json.loads(raw)
        except Exception:
            data = {}

        # BulkSMSBD returns response_code 202 on success
        response_code = data.get('response_code') or data.get('status')
        if response_code in (202, '202', 'success', 'SUCCESS'):
            logger.info(f"SMS sent via BulkSMSBD to={to}")
            return True
        else:
            logger.error(f"BulkSMSBD API error: {raw[:200]}")
            return False
