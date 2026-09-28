from django.urls import path
from apps.storefront.views.home_view import HomeView
from apps.storefront.views.shop_view import ShopView
from apps.storefront.views.product_view import ProductDetailView

app_name = "storefront"

urlpatterns = [
    path("", HomeView.index, name="index"),
    path("shop/", ShopView.shop, name="shop"),
    path("shop/<slug:category_slug>/", ShopView.category_detail, name="category_detail"),
    path("product/<slug:slug>/", ProductDetailView.detail, name="product_detail"),
]