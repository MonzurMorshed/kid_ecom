from django.contrib import admin
from .models import CartItem, ContactMessage, NewsletterSubscriber


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'user', 'session_key', 'product', 'variant', 'quantity', 'unit_price', 'updated_at')
    list_filter   = ('updated_at',)
    search_fields = ('user__username', 'user__email', 'session_key', 'product__title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'subject', 'phone', 'is_read', 'created_at')
    list_filter   = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_read',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display  = ('email', 'is_active', 'created_at')
    list_filter   = ('is_active', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at',)
    list_editable = ('is_active',)
