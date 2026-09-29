from django.urls import path
from apps.storefront.views.home_view import HomeView
from apps.storefront.views.shop_view import ShopView
from apps.storefront.views.product_view import ProductDetailView
from apps.storefront.views.page_view import PageView
from apps.storefront.views.cart_view import (
    cart_page, cart_add, cart_remove, cart_update, cart_count,
    checkout, order_success,
)

app_name = "storefront"

urlpatterns = [
    path("", HomeView.index, name="index"),
    path("shop/", ShopView.shop, name="shop"),
    path("shop/<slug:category_slug>/", ShopView.category_detail, name="category_detail"),
    path("product/<slug:slug>/", ProductDetailView.detail, name="product_detail"),

    # Dynamic pages (Privacy Policy, About Us, etc.)
    path("page/<slug:slug>/", PageView.page_detail, name="page_detail"),

    # ── Cart ──────────────────────────────────────────────────────────────────
    path("cart/",              cart_page,   name="cart"),
    path("cart/add/",          cart_add,    name="cart_add"),
    path("cart/remove/",       cart_remove, name="cart_remove"),
    path("cart/update/",       cart_update, name="cart_update"),
    path("cart/count/",        cart_count,  name="cart_count"),

    # ── Checkout & Orders ─────────────────────────────────────────────────────
    path("checkout/",          checkout,      name="checkout"),
    path("order/<int:pk>/success/", order_success, name="order_success"),
]