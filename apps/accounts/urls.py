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

    # ── Password Reset ────────────────────────────────────────────────────────
    path('forgot-password/',                        views.forgot_password_view,  name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',        views.reset_password_view,   name='reset_password'),
]