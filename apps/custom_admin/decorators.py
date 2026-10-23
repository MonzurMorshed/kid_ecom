from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Ensure the user is authenticated, has staff/superuser access,
    and is neither blocked nor disabled.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/admin/login/?next={request.path}')

        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Admin privileges required to access this page.')
            return redirect('custom_admin:login')

        if getattr(request.user, 'is_blocked', False):
            messages.error(request, 'Your admin account has been temporarily blocked.')
            return redirect('custom_admin:login')

        if not request.user.is_active:
            messages.error(request, 'Your account is currently disabled. Please contact the administrator.')
            return redirect('custom_admin:login')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def permission_required(module_name):
    """
    Ensure the user has permission to access a specific admin module.
    Superadmin and Django superusers bypass all permission checks.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/admin/login/?next={request.path}')

            if not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, 'Admin privileges required to access this page.')
                return redirect('custom_admin:login')

            if getattr(request.user, 'is_blocked', False):
                messages.error(request, 'Your admin account has been temporarily blocked.')
                return redirect('custom_admin:login')

            if not request.user.is_active:
                messages.error(request, 'Your account is currently disabled.')
                return redirect('custom_admin:login')

            # Superusers always have full access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            from .models import AdminProfile
            profile = AdminProfile.get_or_create_for(request.user)

            if profile.has_module_permission(module_name):
                return view_func(request, *args, **kwargs)

            # Denied
            module_title = module_name.replace('_', ' ').title()
            messages.error(request, f'Access Denied: You do not have permission to access {module_title}.')
            return redirect('custom_admin:dashboard')

        return _wrapped_view
    return decorator


def superadmin_required(view_func):
    """
    Strictly require Super Admin role or Django superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/admin/login/?next={request.path}')

        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Admin privileges required.')
            return redirect('custom_admin:login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        from .models import AdminProfile
        profile = AdminProfile.get_or_create_for(request.user)
        if profile.role == 'superadmin':
            return view_func(request, *args, **kwargs)

        messages.error(request, 'Super Admin privileges required to perform this action.')
        return redirect('custom_admin:dashboard')

    return _wrapped_view