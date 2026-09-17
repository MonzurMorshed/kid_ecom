from django.urls import path
from django.views.generic import RedirectView
from . import views
from products import views as product_views

app_name = 'custom_admin'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='custom_admin:dashboard', permanent=False)),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('register/', views.admin_register, name='register'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Categories
    path('categories/', product_views.category_list, name='category_list'),
    path('categories/create/', product_views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', product_views.category_update, name='category_update'),

    # Products
    path('products/', product_views.product_list, name='product_list'),
    path('products/create/', product_views.product_create, name='product_create'),
    path('products/export/', product_views.product_export, name='product_export'),
    path('products/import/', product_views.product_import, name='product_import'),
    path('products/sample-csv/', product_views.product_sample_csv, name='product_sample_csv'),
]