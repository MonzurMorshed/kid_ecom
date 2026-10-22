import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.storage import StaticFilesStorage

try:
    from whitenoise.storage import CompressedStaticFilesStorage
    BaseWhiteNoiseStorage = CompressedStaticFilesStorage
except ImportError:
    BaseWhiteNoiseStorage = StaticFilesStorage


class CdnMediaStorage(FileSystemStorage):
    """
    Production-ready storage that dynamically serves media files through
    a configured CDN (Cloudflare, BunnyCDN, CloudFront) when enabled in
    Developer Settings or via MEDIA_CDN_URL in settings.py / .env.
    """
    def url(self, name):
        # 1. Dynamic SiteSettings override (configured in Developer Settings)
        try:
            from custom_admin.models import SiteSettings
            s = SiteSettings.get_settings()
            if getattr(s, 'enable_cdn', False) and getattr(s, 'media_cdn_url', None):
                cdn = s.media_cdn_url.strip().rstrip('/')
                return f"{cdn}/{name.lstrip('/')}"
        except Exception:
            pass

        # 2. Environment variable override from settings.py
        media_cdn = getattr(settings, 'MEDIA_CDN_URL', None)
        if media_cdn:
            cdn = str(media_cdn).strip().rstrip('/')
            return f"{cdn}/{name.lstrip('/')}"

        # 3. Default FileSystemStorage (/media/...)
        return super().url(name)


class CdnWhiteNoiseStaticStorage(BaseWhiteNoiseStorage):
    """
    WhiteNoise compressed storage with dynamic CDN routing for {% static %} assets.
    """
    def url(self, name):
        try:
            from custom_admin.models import SiteSettings
            s = SiteSettings.get_settings()
            if getattr(s, 'enable_cdn', False) and getattr(s, 'static_cdn_url', None):
                cdn = s.static_cdn_url.strip().rstrip('/')
                res_url = super().url(name)
                if res_url.startswith('/static/'):
                    return f"{cdn}/{res_url[8:].lstrip('/')}"
                return f"{cdn}/{res_url.lstrip('/')}"
        except Exception:
            pass

        static_cdn = getattr(settings, 'STATIC_CDN_URL', None)
        if static_cdn:
            cdn = str(static_cdn).strip().rstrip('/')
            res_url = super().url(name)
            if res_url.startswith('/static/'):
                return f"{cdn}/{res_url[8:].lstrip('/')}"
            return f"{cdn}/{res_url.lstrip('/')}"

        return super().url(name)


class CdnStaticFilesStorage(StaticFilesStorage):
    """
    Standard static files storage with dynamic CDN routing (used in DEBUG mode).
    """
    def url(self, name):
        try:
            from custom_admin.models import SiteSettings
            s = SiteSettings.get_settings()
            if getattr(s, 'enable_cdn', False) and getattr(s, 'static_cdn_url', None):
                cdn = s.static_cdn_url.strip().rstrip('/')
                res_url = super().url(name)
                if res_url.startswith('/static/'):
                    return f"{cdn}/{res_url[8:].lstrip('/')}"
                return f"{cdn}/{res_url.lstrip('/')}"
        except Exception:
            pass

        static_cdn = getattr(settings, 'STATIC_CDN_URL', None)
        if static_cdn:
            cdn = str(static_cdn).strip().rstrip('/')
            res_url = super().url(name)
            if res_url.startswith('/static/'):
                return f"{cdn}/{res_url[8:].lstrip('/')}"
            return f"{cdn}/{res_url.lstrip('/')}"

        return super().url(name)
