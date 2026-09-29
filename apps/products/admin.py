from django.contrib import admin
from .models import Category, Brand, Product, ProductOption, ProductOptionValue, ProductVariant, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active", "parent")
    search_fields = ("name",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "compare_price", "is_active", "is_featured", "is_bestseller", "is_new", "rating", "stock")
    list_editable = ("is_active", "is_featured", "is_bestseller", "is_new")
    list_filter = ("category", "is_active", "is_featured", "is_bestseller", "is_new")
    search_fields = ("title", "description", "long_description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductOptionInline, ProductImageInline]
    fieldsets = (
        (None, {"fields": ("category", "brand", "title", "slug", "description", "long_description")}),
        ("Pricing & Stock", {"fields": ("price", "compare_price", "stock")}),
        ("Storefront Flags", {"fields": ("is_active", "is_featured", "is_bestseller", "is_new", "rating")}),
        ("Soft Delete", {"fields": ("is_deleted", "deleted_at"), "classes": ("collapse",)}),
    )

    class Media:
        js = (
            "https://cdn.ckeditor.com/ckeditor5/41.1.0/classic/ckeditor.js",
            "js/admin_ckeditor.js",
        )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("sku", "product__title")
