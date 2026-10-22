import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import django
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from ..decorators import admin_required
from ..models import ActivityLog, SiteSettings

logger = logging.getLogger('django.request')

ADMIN_NAV_SECTIONS = [
    {
        'title': 'Main Navigation',
        'key': 'main',
        'items': [
            {'key': 'dashboard', 'label': 'Dashboard', 'url_name': 'dashboard', 'icon': 'fa-solid fa-table-cells-large', 'desc': 'Main admin overview, sales metrics, and recent orders'},
            {'key': 'categories', 'label': 'Categories', 'url_name': 'category_list', 'icon': 'fa-solid fa-folder-tree', 'desc': 'Category hierarchy, parent/sub-categories, and sorting'},
            {'key': 'products', 'label': 'Products', 'url_name': 'product_list', 'icon': 'fa-solid fa-box', 'desc': 'Product catalog, prices, stock, images, and discounts'},
            {'key': 'trash', 'label': 'Trash', 'url_name': 'product_trash', 'icon': 'fa-solid fa-trash-can', 'desc': 'Soft-deleted products with restore & permanent delete options'},
            {'key': 'orders', 'label': 'Orders', 'url_name': 'order_list', 'icon': 'fa-solid fa-cart-shopping', 'desc': 'Customer orders, invoices, and fulfillment tracking'},
            {'key': 'customers', 'label': 'Customers', 'url_name': 'customer_list', 'icon': 'fa-solid fa-users', 'desc': 'Customer registered profiles, addresses, and order history'},
        ]
    },
    {
        'title': 'Content & Marketing',
        'key': 'content',
        'items': [
            {'key': 'slider', 'label': 'Hero Slider', 'url_name': 'slider_list', 'icon': 'fa-solid fa-images', 'desc': 'Homepage hero promotional banner carousel'},
            {'key': 'banners', 'label': 'Banners', 'url_name': 'banner_list', 'icon': 'fa-solid fa-rectangle-ad', 'desc': 'Promotional marketing banners across the storefront'},
            {'key': 'pages', 'label': 'Pages', 'url_name': 'page_list', 'icon': 'fa-solid fa-file-lines', 'desc': 'CMS content pages (About, Privacy, Terms, FAQ, etc.)'},
        ]
    },
    {
        'title': 'Store Settings',
        'key': 'settings',
        'items': [
            {'key': 'site_settings', 'label': 'Site Settings', 'url_name': 'site_settings', 'icon': 'fa-solid fa-gear', 'desc': 'Store branding, contact info, currency, shipping & tax'},
            {'key': 'theme_settings', 'label': 'Theme Settings', 'url_name': 'theme_settings', 'icon': 'fa-solid fa-palette', 'desc': 'Customize store colors, header & footer layouts, and UI styling'},
            {'key': 'payment_methods', 'label': 'Payment Methods', 'url_name': 'payment_method_list', 'icon': 'fa-solid fa-credit-card', 'desc': 'Payment gateways (bKash, Nagad, Rocket, Cash on Delivery)'},
        ]
    },
    {
        'title': 'Administration & Security',
        'key': 'administration',
        'items': [
            {'key': 'admin_users', 'label': 'Admin Users', 'url_name': 'admin_user_list', 'icon': 'fa-solid fa-user-shield', 'desc': 'Admin user management and role access control'},
            {'key': 'activity_log', 'label': 'Activity Log', 'url_name': 'activity_log', 'icon': 'fa-solid fa-clipboard-list', 'desc': 'Comprehensive audit trail of administrator actions'},
            {'key': 'locked_users', 'label': 'Locked Accounts', 'url_name': 'locked_users_list', 'icon': 'fa-solid fa-user-lock', 'desc': 'Account lockout and login attempt security monitoring'},
            {'key': 'change_password', 'label': 'Change Password', 'url_name': 'change_password', 'icon': 'fa-solid fa-key', 'desc': 'Update current logged-in admin user password'},
        ]
    },
]

VALID_NAV_KEYS = {item['key'] for section in ADMIN_NAV_SECTIONS for item in section['items']}


def _format_size(size_bytes):
    """Formats bytes to human-readable size string."""
    try:
        size_bytes = int(size_bytes)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    except Exception:
        return "0 B"


@admin_required
def developer_settings(request):
    """
    Developer Settings view:
    - Server and Environment information
    - Storefront Maintenance Mode toggle & custom message
    - In-memory cache status & clear action
    - Error log inspection (size, timestamp, contents)
    - Error log clear action
    """
    try:
        site_settings_obj = SiteSettings.get_settings()
    except Exception as e:
        logger.error(f"Error getting SiteSettings in developer_settings: {e}", exc_info=True)
        site_settings_obj = SiteSettings(pk=1, site_name='Kidurabd')

    # Handle Maintenance Mode Update
    if request.method == 'POST' and 'update_maintenance' in request.POST:
        mode = request.POST.get('maintenance_mode') == 'on'
        msg = request.POST.get('maintenance_msg', '').strip()
        try:
            site_settings_obj.maintenance_mode = mode
            if msg:
                site_settings_obj.maintenance_msg = msg
            site_settings_obj.save(update_fields=['maintenance_mode', 'maintenance_msg'])

            from django.core.cache import cache
            try:
                cache.clear()
            except Exception:
                pass

            ActivityLog.log(
                request=request,
                action='toggle',
                description=f'Changed Maintenance Mode to {"ENABLED (Storefront Offline)" if mode else "DISABLED (Storefront Live)"}.',
                target_type='Maintenance',
            )
            messages.success(request, f'Maintenance mode has been {"ENABLED" if mode else "DISABLED"} successfully.')
        except Exception as e:
            logger.error(f"Failed to update maintenance settings: {e}", exc_info=True)
            messages.error(request, f"Failed to update maintenance mode: {e}")
        return redirect('custom_admin:developer_settings')

    # Handle Navigation Menus Visibility Update
    if request.method == 'POST' and 'update_hidden_menus' in request.POST:
        submitted_hidden = request.POST.getlist('hidden_menus')
        valid_hidden = [k for k in submitted_hidden if k in VALID_NAV_KEYS]
        try:
            site_settings_obj.hidden_menus = valid_hidden
            site_settings_obj.save(update_fields=['hidden_menus'])

            from django.core.cache import cache
            try:
                cache.clear()
            except Exception:
                pass

            hidden_count = len(valid_hidden)
            desc = f"Updated sidebar menu visibility: {hidden_count} menu(s) hidden ({', '.join(valid_hidden) if valid_hidden else 'none'})."
            ActivityLog.log(
                request=request,
                action='settings',
                description=desc,
                target_type='Developer Settings',
            )
            messages.success(request, f'Sidebar menu visibility updated successfully. {hidden_count} menu(s) currently hidden.')
        except Exception as e:
            logger.error(f"Failed to update menu visibility: {e}", exc_info=True)
            messages.error(request, f"Failed to update menu visibility: {e}")
        return redirect('custom_admin:developer_settings')

    # Handle Image Optimization Settings Update
    if request.method == 'POST' and 'update_image_settings' in request.POST:
        try:
            img_format   = request.POST.get('img_format', 'WEBP').upper()
            img_quality  = max(1, min(100, int(request.POST.get('img_quality', 82))))
            img_max_w    = max(100, min(4000, int(request.POST.get('img_max_width', 1200))))
            img_max_h    = max(100, min(4000, int(request.POST.get('img_max_height', 1200))))
            img_thumb_w  = max(50,  min(1000, int(request.POST.get('img_thumb_width', 400))))
            img_thumb_h  = max(50,  min(1000, int(request.POST.get('img_thumb_height', 400))))
            img_hero_w   = max(400, min(4000, int(request.POST.get('img_hero_width', 1600))))
            img_hero_h   = max(200, min(3000, int(request.POST.get('img_hero_height', 900))))
            img_lazy     = request.POST.get('img_lazy_loading') == 'on'

            if img_format not in ('WEBP', 'JPEG', 'PNG'):
                img_format = 'WEBP'

            site_settings_obj.img_format      = img_format
            site_settings_obj.img_quality     = img_quality
            site_settings_obj.img_max_width   = img_max_w
            site_settings_obj.img_max_height  = img_max_h
            site_settings_obj.img_thumb_width  = img_thumb_w
            site_settings_obj.img_thumb_height = img_thumb_h
            site_settings_obj.img_hero_width   = img_hero_w
            site_settings_obj.img_hero_height  = img_hero_h
            site_settings_obj.img_lazy_loading = img_lazy
            site_settings_obj.save(update_fields=[
                'img_format', 'img_quality',
                'img_max_width', 'img_max_height',
                'img_thumb_width', 'img_thumb_height',
                'img_hero_width', 'img_hero_height',
                'img_lazy_loading',
            ])

            from django.core.cache import cache
            try:
                cache.clear()
            except Exception:
                pass

            ActivityLog.log(
                request=request,
                action='settings',
                description=(
                    f"Updated Image Optimization: format={img_format}, quality={img_quality}, "
                    f"max={img_max_w}×{img_max_h}, thumb={img_thumb_w}×{img_thumb_h}, "
                    f"hero={img_hero_w}×{img_hero_h}, lazy={img_lazy}."
                ),
                target_type='Developer Settings',
            )
            messages.success(request, 'Image optimization settings saved. New uploads will use these settings.')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid value in image settings: {e}')
        except Exception as e:
            logger.error(f"Failed to update image settings: {e}", exc_info=True)
        return redirect('custom_admin:developer_settings')

    # Handle Bulk Image Optimization Trigger
    if request.method == 'POST' and 'bulk_optimize_images' in request.POST:
        try:
            from products.image_optimizer import bulk_optimize_all_media
            stats = bulk_optimize_all_media()
            saved_mb = round(stats['saved_bytes'] / (1024 * 1024), 2)
            saved_kb = round(stats['saved_bytes'] / 1024, 1)

            ActivityLog.log(
                request=request,
                action='settings',
                description=(
                    f"Bulk image optimization: {stats['processed']} optimized, "
                    f"{stats['skipped']} skipped, {stats['errors']} errors, {saved_mb} MB saved."
                ),
                target_type='Developer Settings',
            )

            if stats['errors'] == 0:
                messages.success(
                    request,
                    f"🎉 Successfully optimized {stats['processed']} image(s)! Saved {saved_mb} MB ({saved_kb} KB) of storage & bandwidth."
                )
            else:
                messages.warning(
                    request,
                    f"Optimized {stats['processed']} images with {stats['errors']} error(s). Saved {saved_mb} MB."
                )
        except Exception as e:
            logger.error(f"Bulk image optimization failed: {e}", exc_info=True)
            messages.error(request, f"Bulk image optimization failed: {e}")
        return redirect('custom_admin:developer_settings')

    # Handle CDN Settings Update
    if request.method == 'POST' and 'update_cdn_settings' in request.POST:
        try:
            enable_cdn = request.POST.get('enable_cdn') == 'on'
            static_cdn_url = request.POST.get('static_cdn_url', '').strip()
            media_cdn_url = request.POST.get('media_cdn_url', '').strip()
            cf_zone_id = request.POST.get('cloudflare_zone_id', '').strip()
            cf_api_token = request.POST.get('cloudflare_api_token', '').strip()

            site_settings_obj.enable_cdn = enable_cdn
            site_settings_obj.static_cdn_url = static_cdn_url or None
            site_settings_obj.media_cdn_url = media_cdn_url or None
            site_settings_obj.cloudflare_zone_id = cf_zone_id or None
            if cf_api_token and not cf_api_token.startswith('•'):
                site_settings_obj.cloudflare_api_token = cf_api_token

            site_settings_obj.save(update_fields=[
                'enable_cdn', 'static_cdn_url', 'media_cdn_url',
                'cloudflare_zone_id', 'cloudflare_api_token',
            ])

            from django.core.cache import cache
            try:
                cache.clear()
            except Exception:
                pass

            status_str = "ENABLED" if enable_cdn else "DISABLED"
            ActivityLog.log(
                request=request,
                action='settings',
                description=f"Updated CDN Settings: status={status_str}, static={static_cdn_url or 'local'}, media={media_cdn_url or 'local'}.",
                target_type='Developer Settings',
            )
            messages.success(request, f"CDN configuration saved ({status_str}).")
        except Exception as e:
            logger.error(f"Failed to update CDN settings: {e}", exc_info=True)
            messages.error(request, f"Failed to save CDN settings: {e}")
        return redirect('custom_admin:developer_settings')

    # Handle Cloudflare Cache Purge Action
    if request.method == 'POST' and 'purge_cloudflare_cache' in request.POST:
        from custom_admin.cloudflare import purge_cloudflare_cache
        success, msg = purge_cloudflare_cache()
        if success:
            ActivityLog.log(
                request=request,
                action='settings',
                description="Purged Cloudflare CDN cache globally.",
                target_type='Developer Settings',
            )
            messages.success(request, f"🧹 {msg}")
        else:
            messages.error(request, f"Cloudflare Purge Failed: {msg}")
        return redirect('custom_admin:developer_settings')

    # Handle Run Collectstatic
    if request.method == 'POST' and 'run_collectstatic' in request.POST:
        from io import StringIO
        from django.core.management import call_command
        try:
            out = StringIO()
            call_command('collectstatic', interactive=False, verbosity=1, stdout=out)
            output_msg = out.getvalue().strip()
            summary_line = output_msg.splitlines()[-1] if output_msg else 'Static files collected.'

            ActivityLog.log(
                request=request,
                action='settings',
                description=f"Executed collectstatic from Developer Settings: {summary_line}",
                target_type='Developer Settings',
            )
            messages.success(request, f"📦 {summary_line}")
        except Exception as e:
            logger.error(f"Collectstatic failed: {e}", exc_info=True)
            messages.error(request, f"Collectstatic execution failed: {e}")
        return redirect('custom_admin:developer_settings')




    log_file = getattr(settings, 'ERROR_LOG_FILE', settings.BASE_DIR / 'logs' / 'error.log')

    # Ensure log directory & file exists (safely handle permission errors)
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.touch()
    except Exception as e:
        logger.warning(f"Could not prepare log file {log_file}: {e}")

    # Read log file details
    log_exists = False
    log_size = 0
    log_size_formatted = "0 B"
    log_lines = []
    log_line_count = 0
    last_modified = None

    try:
        if hasattr(log_file, 'exists') and log_file.exists():
            log_exists = True
            stat = log_file.stat()
            log_size = stat.st_size
            log_size_formatted = _format_size(log_size)
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            if log_size > 0:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    all_lines = f.readlines()
                    log_line_count = len(all_lines)
                    # Display the latest 500 lines to keep UI fast and responsive
                    log_lines = [line.rstrip('\r\n') for line in all_lines[-500:]]
    except Exception as e:
        log_lines = [f"Note: Error log not readable or empty: {str(e)}"]

    # Passenger restart timestamp
    restart_time = None
    try:
        restart_file = settings.BASE_DIR / 'tmp' / 'restart.txt'
        if restart_file.exists():
            restart_time = datetime.fromtimestamp(restart_file.stat().st_mtime)
    except Exception:
        pass

    # Cache info
    caches_cfg = getattr(settings, 'CACHES', {})
    if isinstance(caches_cfg, dict):
        cache_backend = str(caches_cfg.get('default', {}).get('BACKEND', 'LocMemCache'))
    else:
        cache_backend = 'LocMemCache'

    # Database info
    databases_cfg = getattr(settings, 'DATABASES', {})
    if isinstance(databases_cfg, dict):
        db_config = databases_cfg.get('default', {})
    else:
        db_config = {}

    engine_raw = db_config.get('ENGINE') or ''
    db_engine = str(engine_raw).split('.')[-1] if engine_raw else 'mysql'
    db_name = str(db_config.get('NAME') or 'kidurabd_db')
    db_host = str(db_config.get('HOST') or '127.0.0.1')
    db_port = str(db_config.get('PORT') or '3306')

    # Storage & Static/Media statistics
    static_file_count, static_total_size = 0, 0
    media_file_count, media_total_size = 0, 0
    try:
        static_dir = settings.BASE_DIR / 'static'
        if static_dir.exists():
            for root, _, files in os.walk(static_dir):
                static_file_count += len(files)
                for f in files:
                    try:
                        static_total_size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        media_dir = settings.BASE_DIR / 'media'
        if media_dir.exists():
            for root, _, files in os.walk(media_dir):
                media_file_count += len(files)
                for f in files:
                    try:
                        media_total_size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
    except Exception:
        pass

    context = {
        'python_version': sys.version.split()[0],
        'django_version': django.get_version(),
        'debug_mode': getattr(settings, 'DEBUG', False),
        'cache_backend': cache_backend,
        'db_engine': db_engine,
        'db_name': db_name,
        'db_host': db_host,
        'db_port': db_port,
        'restart_time': restart_time,
        'log_file_path': str(log_file),
        'log_exists': log_exists,
        'log_size_bytes': log_size,
        'log_size_formatted': log_size_formatted,
        'log_line_count': log_line_count,
        'log_lines': log_lines,
        'log_text': '\n'.join(log_lines),
        'last_modified': last_modified,
        'settings': site_settings_obj,
        'maintenance_mode': getattr(site_settings_obj, 'maintenance_mode', False),
        'maintenance_msg': getattr(site_settings_obj, 'maintenance_msg', ''),
        'nav_menu_sections': ADMIN_NAV_SECTIONS,
        'hidden_menus': site_settings_obj.hidden_menu_list,
        'hidden_menu_count': len(site_settings_obj.hidden_menu_list),
        # Image optimization settings
        'img_format':       getattr(site_settings_obj, 'img_format', 'WEBP'),
        'img_quality':      getattr(site_settings_obj, 'img_quality', 82),
        'img_max_width':    getattr(site_settings_obj, 'img_max_width', 1200),
        'img_max_height':   getattr(site_settings_obj, 'img_max_height', 1200),
        'img_thumb_width':  getattr(site_settings_obj, 'img_thumb_width', 400),
        'img_thumb_height': getattr(site_settings_obj, 'img_thumb_height', 400),
        'img_hero_width':   getattr(site_settings_obj, 'img_hero_width', 1600),
        'img_hero_height':  getattr(site_settings_obj, 'img_hero_height', 900),
        'img_lazy_loading': getattr(site_settings_obj, 'img_lazy_loading', True),
        # CDN & Static Storage settings
        'enable_cdn':                  getattr(site_settings_obj, 'enable_cdn', False),
        'static_cdn_url':              getattr(site_settings_obj, 'static_cdn_url', '') or '',
        'media_cdn_url':               getattr(site_settings_obj, 'media_cdn_url', '') or '',
        'cloudflare_zone_id':          getattr(site_settings_obj, 'cloudflare_zone_id', '') or getattr(settings, 'CLOUDFLARE_ZONE_ID', '') or '',
        'has_cloudflare_token':        bool(getattr(site_settings_obj, 'cloudflare_api_token', None) or getattr(settings, 'CLOUDFLARE_API_TOKEN', None)),
        'cloudflare_api_token_masked': '••••••••••••••••' if (getattr(site_settings_obj, 'cloudflare_api_token', None) or getattr(settings, 'CLOUDFLARE_API_TOKEN', None)) else '',
        'static_file_count':           static_file_count,
        'static_total_size':           _format_size(static_total_size),
        'media_file_count':            media_file_count,
        'media_total_size':            _format_size(media_total_size),
        'whitenoise_active':           not getattr(settings, 'DEBUG', False),
        'current_static_url':          getattr(settings, 'STATIC_URL', '/static/'),
        'current_media_url':           getattr(settings, 'MEDIA_URL', '/media/'),
    }
    return render(request, 'custom_admin/settings/developer_settings.html', context)


@admin_required
@require_POST
def clear_error_log(request):
    """
    Clears / truncates the application error.log file and records the action in ActivityLog.
    """
    log_file = getattr(settings, 'ERROR_LOG_FILE', settings.BASE_DIR / 'logs' / 'error.log')

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.truncate(0)

        ActivityLog.log(
            request=request,
            action='settings',
            description='Cleared application error log (error.log).',
            target_type='Developer Settings',
        )
        messages.success(request, 'Error log has been cleared successfully.')
    except Exception as e:
        messages.error(request, f'Failed to clear error log: {str(e)}')

    return redirect('custom_admin:developer_settings')
