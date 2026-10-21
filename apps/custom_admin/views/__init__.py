from .auth import (
    admin_login,
    admin_register,
    admin_logout,
    admin_forgot_password,
    admin_reset_password,
)
from .dashboard import (
    dashboard,
    revenue_chart_data,
)
from .settings import (
    site_settings,
    theme_settings,
    payment_method_list,
    payment_method_create,
    payment_method_edit,
    payment_method_toggle,
    payment_method_delete,
    clear_cache,
)
from .developer import (
    developer_settings,
    clear_error_log,
)
from .content import (
    slider_list,
    slider_create,
    slider_edit,
    slider_toggle,
    slider_delete,
    banner_list,
    banner_create,
    banner_edit,
    banner_toggle,
    banner_delete,
)
from .admin_users import (
    admin_user_list,
    admin_user_edit,
    admin_user_toggle,
    change_password,
    activity_log,
    activity_log_clear,
    locked_users_list,
    locked_user_unlock,
    locked_users_reset_all,
    settings_admin_list,
    settings_change_password,
    settings_admin_role_toggle,
    settings_admin_remove,
)
from .customers import (
    customer_list,
    customer_detail,
    customer_block_toggle,
)
from .pages import (
    page_list,
    page_create,
    page_edit,
    page_toggle,
    page_delete,
)

__all__ = [
    # Auth
    'admin_login',
    'admin_register',
    'admin_logout',
    'admin_forgot_password',
    'admin_reset_password',
    # Dashboard
    'dashboard',
    'revenue_chart_data',
    # Settings & Payment
    'site_settings',
    'theme_settings',
    'payment_method_list',
    'payment_method_create',
    'payment_method_edit',
    'payment_method_toggle',
    'payment_method_delete',
    'clear_cache',
    'developer_settings',
    'clear_error_log',
    # Content
    'slider_list',
    'slider_create',
    'slider_edit',
    'slider_toggle',
    'slider_delete',
    'banner_list',
    'banner_create',
    'banner_edit',
    'banner_toggle',
    'banner_delete',
    # Admin Users
    'admin_user_list',
    'admin_user_edit',
    'admin_user_toggle',
    'change_password',
    'activity_log',
    'activity_log_clear',
    'locked_users_list',
    'locked_user_unlock',
    'locked_users_reset_all',
    'settings_admin_list',
    'settings_change_password',
    'settings_admin_role_toggle',
    'settings_admin_remove',
    # Customers
    'customer_list',
    'customer_detail',
    'customer_block_toggle',
    # Pages
    'page_list',
    'page_create',
    'page_edit',
    'page_toggle',
    'page_delete',
]
