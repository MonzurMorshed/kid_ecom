from django.urls import path, include
from django.views.generic import RedirectView
from . import views

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
]