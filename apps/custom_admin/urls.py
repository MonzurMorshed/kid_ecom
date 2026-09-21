from django.urls import path, include
from django.views.generic import RedirectView
from . import views
from accounts import views as accounts_views

app_name = 'custom_admin'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='custom_admin:dashboard', permanent=False)),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('register/', views.admin_register, name='register'),
    path('logout/', views.admin_logout, name='logout'),

    # Products & Categories (delegated to products app)
    path('', include('products.urls')),
    # Orders
    path('', include('orders.urls')),

    # Customers
    path('customers/',                              accounts_views.customer_list,          name='customer_list'),
    path('customers/<int:pk>/',                     accounts_views.customer_detail,        name='customer_detail'),
    path('customers/<int:pk>/block-toggle/',        accounts_views.customer_block_toggle,  name='customer_block_toggle'),

    # Settings
    path('settings/',                               views.settings_admin_list,             name='settings_admin_list'),
    path('settings/change-password/',               views.settings_change_password,        name='settings_change_password'),
    path('settings/admins/<int:pk>/role-toggle/',   views.settings_admin_role_toggle,      name='settings_admin_role_toggle'),
    path('settings/admins/<int:pk>/remove/',        views.settings_admin_remove,           name='settings_admin_remove'),
]