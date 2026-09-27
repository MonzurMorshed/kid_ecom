from django.urls import path
from apps.storefront.views.home_view import HomeView

urlpatterns = [
    path('', HomeView.index, name='index'),
]