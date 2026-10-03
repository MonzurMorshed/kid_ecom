from django.contrib import admin
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'user', 'session_key', 'product', 'variant', 'quantity', 'unit_price', 'updated_at')
    list_filter   = ('updated_at',)
    search_fields = ('user__username', 'user__email', 'session_key', 'product__title')
    readonly_fields = ('created_at', 'updated_at')
