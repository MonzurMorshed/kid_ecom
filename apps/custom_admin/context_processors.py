from .models import AdminProfile
from .permissions import ALL_PERMISSION_IDS, DEFAULT_ROLE_PERMISSIONS


def admin_permissions(request):
    """
    Context processor that supplies role and active permissions to custom admin templates.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}

    try:
        profile = getattr(request.user, 'admin_profile', None)
        if not profile:
            profile = AdminProfile.get_or_create_for(request.user)
    except Exception:
        profile = None

    if not profile:
        return {}

    is_super = request.user.is_superuser or profile.role == 'superadmin'
    user_perms = profile.get_effective_permissions()

    return {
        'admin_profile': profile,
        'admin_role': profile.role,
        'user_permissions': user_perms,
        'is_superadmin': is_super,
        'is_manager': profile.role == 'manager',
        'is_staff_role': profile.role == 'staff',
    }
