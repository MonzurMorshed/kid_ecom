import json
import logging
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)


def purge_cloudflare_cache(zone_id=None, api_token=None):
    """
    Sends a request to Cloudflare API v4 to purge all cached assets globally.
    Returns (success: bool, message: str).
    """
    if not zone_id or not api_token:
        try:
            from custom_admin.models import SiteSettings
            s = SiteSettings.get_settings()
            zone_id = zone_id or getattr(s, 'cloudflare_zone_id', None)
            api_token = api_token or getattr(s, 'cloudflare_api_token', None)
        except Exception:
            pass

    zone_id = zone_id or getattr(settings, 'CLOUDFLARE_ZONE_ID', None)
    api_token = api_token or getattr(settings, 'CLOUDFLARE_API_TOKEN', None)

    if not zone_id:
        return False, "Cloudflare Zone ID is missing. Please save your Zone ID in Developer Settings."
    if not api_token:
        return False, "Cloudflare API Token is missing. Please save your API Token in Developer Settings."

    zone_id = str(zone_id).strip()
    api_token = str(api_token).strip()

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "User-Agent": "Kidurabd-App/1.0",
    }
    payload = json.dumps({"purge_everything": True}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            resp_body = response.read().decode("utf-8")
            data = json.loads(resp_body)
            if data.get("success"):
                return True, "Cloudflare CDN cache purged globally across all edge locations!"
            errors = data.get("errors", [])
            err_msg = errors[0].get("message") if errors else "Unknown API error"
            return False, f"Cloudflare API Error: {err_msg}"
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            data = json.loads(err_body)
            errors = data.get("errors", [])
            err_msg = errors[0].get("message") if errors else e.reason
            return False, f"Cloudflare Error ({e.code}): {err_msg}"
        except Exception:
            return False, f"Cloudflare Error ({e.code}): {e.reason}"
    except Exception as e:
        logger.error(f"Failed to purge Cloudflare cache: {e}", exc_info=True)
        return False, f"Network connection failed: {str(e)}"
