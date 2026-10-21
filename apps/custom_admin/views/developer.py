import sys
import os
from datetime import datetime
from pathlib import Path
import django
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from ..decorators import admin_required
from ..models import ActivityLog, SiteSettings


def _format_size(size_bytes):
    """Formats bytes to human-readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


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
    site_settings_obj = SiteSettings.get_settings()

    # Handle Maintenance Mode Update
    if request.method == 'POST' and 'update_maintenance' in request.POST:
        mode = request.POST.get('maintenance_mode') == 'on'
        msg = request.POST.get('maintenance_msg', '').strip()
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
        return redirect('custom_admin:developer_settings')

    log_file = getattr(settings, 'ERROR_LOG_FILE', settings.BASE_DIR / 'logs' / 'error.log')

    # Ensure log directory & file exists
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.touch()
    except Exception:
        pass

    # Read log file details
    log_exists = log_file.exists()
    log_size = 0
    log_size_formatted = "0 B"
    log_lines = []
    log_line_count = 0
    last_modified = None

    if log_exists:
        try:
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
            log_lines = [f"Error reading log file: {str(e)}"]

    # Passenger restart timestamp
    restart_file = settings.BASE_DIR / 'tmp' / 'restart.txt'
    restart_time = None
    if restart_file.exists():
        try:
            restart_time = datetime.fromtimestamp(restart_file.stat().st_mtime)
        except Exception:
            pass

    # Cache info
    cache_backend = settings.CACHES.get('default', {}).get('BACKEND', 'Unknown')

    # Database info
    db_config = settings.DATABASES.get('default', {})
    db_engine = db_config.get('ENGINE', '').split('.')[-1]
    db_name = db_config.get('NAME', '')
    db_host = db_config.get('HOST', '127.0.0.1')
    db_port = db_config.get('PORT', '3306')

    context = {
        'python_version': sys.version.split()[0],
        'django_version': django.get_version(),
        'debug_mode': settings.DEBUG,
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
        'log_text': ''.join(log_lines),
        'last_modified': last_modified,
        'settings': site_settings_obj,
        'maintenance_mode': site_settings_obj.maintenance_mode,
        'maintenance_msg': site_settings_obj.maintenance_msg,
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
