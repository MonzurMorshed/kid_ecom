from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ── Auth ─────────────────────────────────────────────────────────────────
    path('register/',                               views.register_view,       name='register'),
    path('login/',                                  views.login_view,          name='login'),
    path('logout/',                                 views.logout_view,         name='logout'),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile/',                                views.profile_view,        name='profile'),
    path('profile/edit/',                           views.profile_edit,        name='profile_edit'),
    path('profile/change-password/',                views.change_password_view, name='change_password'),

    # ── Orders ────────────────────────────────────────────────────────────────
    path('orders/<int:pk>/',                        views.order_detail,        name='order_detail'),

    # ── Wishlist ──────────────────────────────────────────────────────────────
    path('wishlist/',                               views.wishlist_page,       name='wishlist'),
    path('wishlist/toggle/',                        views.wishlist_toggle,     name='wishlist_toggle'),

    # ── Review History ────────────────────────────────────────────────────────
    path('reviews/',                                views.review_history,      name='review_history'),

    # ── Address Book ──────────────────────────────────────────────────────────
    path('addresses/',                              views.address_list,        name='address_list'),
    path('addresses/add/',                          views.address_create,      name='address_create'),
    path('addresses/<int:pk>/edit/',                views.address_edit,        name='address_edit'),
    path('addresses/<int:pk>/delete/',              views.address_delete,      name='address_delete'),
    path('addresses/<int:pk>/default/',             views.address_set_default, name='address_set_default'),

    # ── Password Reset ────────────────────────────────────────────────────────
    path('forgot-password/',                        views.forgot_password_view,  name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',        views.reset_password_view,   name='reset_password'),
]