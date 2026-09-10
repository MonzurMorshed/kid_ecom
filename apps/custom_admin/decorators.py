from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied('You are not authorized to access this page')
    return _wrapped_view
    