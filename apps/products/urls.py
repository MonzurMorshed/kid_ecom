from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/toggle/', views.category_toggle, name='category_toggle'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_details, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_soft_delete, name='product_delete'),
    path('products/<int:pk>/options/add/', views.option_add, name='option_add'),
    path('products/options/<int:option_pk>/delete/', views.option_delete, name='option_delete'),
    path('products/options/<int:option_pk>/values/add/', views.option_value_add, name='option_value_add'),
    path('products/options/values/<int:value_pk>/delete/', views.option_value_delete, name='option_value_delete'),
    path('products/images/<int:image_pk>/delete/', views.product_image_delete, name='product_image_delete'),
    path('products/images/<int:image_pk>/alt/', views.image_alt_update, name='image_alt_update'),
    path('products/<int:pk>/images/reorder/', views.image_reorder, name='image_reorder'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/export/', views.product_export, name='product_export'),
    path('products/import/', views.product_import, name='product_import'),
    path('products/sample-csv/', views.product_sample_csv, name='product_sample_csv'),
    path('products/trash/', views.product_trash, name='product_trash'),
    path('products/<int:pk>/restore/', views.product_restore, name='product_restore'),
    path('products/<int:pk>/permanent-delete/', views.product_permanent_delete, name='product_permanent_delete'),

    # Variants
    path('products/variants/<int:variant_pk>/update/', views.variant_update, name='variant_update'),
    path('products/variants/<int:variant_pk>/image/', views.variant_image_upload, name='variant_image_upload'),
]

