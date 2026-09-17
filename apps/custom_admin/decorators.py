from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Admin privileges required to access this page.')
                return redirect('custom_admin:login')
        else:
            return redirect(f'/admin/login/?next={request.path}')
    return _wrapped_view