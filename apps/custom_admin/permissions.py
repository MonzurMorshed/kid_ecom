"""
Permission definitions and role-based presets for Custom Admin.
"""

AVAILABLE_PERMISSIONS = [
    {
        'id': 'dashboard',
        'name': 'Dashboard Overview',
        'group': 'General',
        'icon': 'fa-solid fa-chart-line',
        'description': 'View dashboard statistics, orders metrics, and revenue charts'
    },
    {
        'id': 'categories',
        'name': 'Categories',
        'group': 'Catalog',
        'icon': 'fa-solid fa-folder-tree',
        'description': 'Create, edit, toggle and organize product categories'
    },
    {
        'id': 'products',
        'name': 'Products & Inventory',
        'group': 'Catalog',
        'icon': 'fa-solid fa-box-open',
        'description': 'Manage products, stock variants, CSV import/export, and trash'
    },
    {
        'id': 'orders',
        'name': 'Orders Management',
        'group': 'Sales',
        'icon': 'fa-solid fa-receipt',
        'description': 'View, process, cancel orders, update status, and print invoices'
    },
    {
        'id': 'customers',
        'name': 'Customers',
        'group': 'Sales',
        'icon': 'fa-solid fa-users',
        'description': 'View customer profiles, order history, and toggle account blocks'
    },
    {
        'id': 'content',
        'name': 'Content & Media (CMS)',
        'group': 'Content',
        'icon': 'fa-solid fa-photo-film',
        'description': 'Manage hero sliders, promotional banners, and custom pages'
    },
    {
        'id': 'settings',
        'name': 'Store & Theme Settings',
        'group': 'Administration',
        'icon': 'fa-solid fa-sliders',
        'description': 'Manage site identity, announcement bar, maintenance mode, and colors'
    },
    {
        'id': 'payment_methods',
        'name': 'Payment Methods',
        'group': 'Administration',
        'icon': 'fa-solid fa-credit-card',
        'description': 'Configure bKash, Nagad, Rocket, COD and bank transfer options'
    },
    {
        'id': 'admin_users',
        'name': 'Staff & Admin Management',
        'group': 'Security & Administration',
        'icon': 'fa-solid fa-user-shield',
        'description': 'Create staff accounts, assign roles, and configure dynamic permissions'
    },
    {
        'id': 'activity_log',
        'name': 'Activity & Audit Log',
        'group': 'Security & Administration',
        'icon': 'fa-solid fa-clipboard-list',
        'description': 'Inspect admin logins, changes, updates, and system audit trail'
    },
    {
        'id': 'security',
        'name': 'Security & Locked Accounts',
        'group': 'Security & Administration',
        'icon': 'fa-solid fa-lock',
        'description': 'View brute-force failed login attempts and unlock IP/accounts'
    },
    {
        'id': 'developer',
        'name': 'Developer Tools',
        'group': 'System',
        'icon': 'fa-solid fa-terminal',
        'description': 'Clear server cache, inspect error logs, and developer utilities'
    },
]

ALL_PERMISSION_IDS = [p['id'] for p in AVAILABLE_PERMISSIONS]

DEFAULT_ROLE_PERMISSIONS = {
    'superadmin': ALL_PERMISSION_IDS,
    'manager': [
        'dashboard',
        'categories',
        'products',
        'orders',
        'customers',
        'content',
    ],
    'staff': [
        'dashboard',
        'products',
        'orders',
    ],
}


def get_permissions_by_group():
    """Group permissions for structured display in admin edit UI."""
    groups = {}
    for p in AVAILABLE_PERMISSIONS:
        group_name = p['group']
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(p)
    return groups
