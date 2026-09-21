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
    path('forgot-password/', views.admin_forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.admin_reset_password, name='reset_password'),

    # Products & Categories (delegated to products app)
    path('', include('products.urls')),
    # Orders
    path('', include('orders.urls')),

    # ── Site Settings ──────────────────────────────────────────────────────────
    path('settings/', views.site_settings, name='site_settings'),

    # ── Payment Methods ────────────────────────────────────────────────────────
    path('settings/payment-methods/', views.payment_method_list, name='payment_method_list'),
    path('settings/payment-methods/add/', views.payment_method_create, name='payment_method_create'),
    path('settings/payment-methods/<int:pk>/edit/', views.payment_method_edit, name='payment_method_edit'),
    path('settings/payment-methods/<int:pk>/toggle/', views.payment_method_toggle, name='payment_method_toggle'),
    path('settings/payment-methods/<int:pk>/delete/', views.payment_method_delete, name='payment_method_delete'),

    # ── Hero Slider ────────────────────────────────────────────────────────────
    path('content/slider/', views.slider_list, name='slider_list'),
    path('content/slider/add/', views.slider_create, name='slider_create'),
    path('content/slider/<int:pk>/edit/', views.slider_edit, name='slider_edit'),
    path('content/slider/<int:pk>/toggle/', views.slider_toggle, name='slider_toggle'),
    path('content/slider/<int:pk>/delete/', views.slider_delete, name='slider_delete'),

    # ── Banners ────────────────────────────────────────────────────────────────
    path('content/banners/', views.banner_list, name='banner_list'),
    path('content/banners/add/', views.banner_create, name='banner_create'),
    path('content/banners/<int:pk>/edit/', views.banner_edit, name='banner_edit'),
    path('content/banners/<int:pk>/toggle/', views.banner_toggle, name='banner_toggle'),
    path('content/banners/<int:pk>/delete/', views.banner_delete, name='banner_delete'),

    # ── Admin User Management ──────────────────────────────────────────────────
    path('admin-users/', views.admin_user_list, name='admin_user_list'),
    path('admin-users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin-users/<int:pk>/toggle/', views.admin_user_toggle, name='admin_user_toggle'),
    path('admin-users/<int:pk>/reset-password/', views.change_password, name='admin_reset_password'),

    # ── Change Own Password ────────────────────────────────────────────────────
    path('my-password/', views.change_password, name='change_password'),

    # ── Activity Log ───────────────────────────────────────────────────────────
    path('activity-log/', views.activity_log, name='activity_log'),
    path('activity-log/clear/', views.activity_log_clear, name='activity_log_clear'),
]