from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='custom_admin:dashboard', permanent=False)),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('products/', views.product_list, name='product_list'),
    # path('products/create/', views.product_create, name='product_create'),
]