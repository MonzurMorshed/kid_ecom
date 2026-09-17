from django.db import models


# =========================================================
# Category
# =========================================================

class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)

    # Parent category / Subcategory
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )

    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["created_at"]

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"

        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def is_subcategory(self):
        return self.parent is not None



# =========================================================
# Brand
# =========================================================

class Brand(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)

    logo = models.ImageField(
        upload_to="brands/",
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ["created_at"]

    def __str__(self):
        return self.name


# =========================================================
# Product
# =========================================================

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
    )

    brand = models.ForeignKey(
        Brand,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=500)

    slug = models.SlugField(
        max_length=500,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    # For simple product.
    # Variant product stock should ideally be managed
    # from ProductVariant.stock.
    stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["created_at"]

    def __str__(self):
        return self.title


# =========================================================
# Product Option
# Example:
# Product = T-Shirt
# Option = Size
# Option = Color
# =========================================================

class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="options",
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        max_length=100,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Option"
        verbose_name_plural = "Product Options"
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["product", "name"],
                name="unique_product_option_name",
            )
        ]

    def __str__(self):
        return f"{self.product.title} - {self.name}"


# =========================================================
# Product Option Value
#
# Example:
# Size:
#   Small
#   Medium
#   Large
#
# Color:
#   Red
#   Blue
#   Black
# =========================================================

class ProductOptionValue(models.Model):
    option = models.ForeignKey(
        ProductOption,
        related_name="values",
        on_delete=models.CASCADE,
    )

    value = models.CharField(
        max_length=100,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Option Value"
        verbose_name_plural = "Product Option Values"
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["option", "value"],
                name="unique_product_option_value",
            )
        ]

    def __str__(self):
        return (
            f"{self.option.product.title} - "
            f"{self.option.name}: {self.value}"
        )


# =========================================================
# Product Variant
#
# Example:
#
# T-Shirt
#
# Variant 1:
#   Size = Small
#   Color = Red
#   SKU = TS-S-RED
#
# Variant 2:
#   Size = Medium
#   Color = Red
#   SKU = TS-M-RED
# =========================================================

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE,
    )

    # Variant is connected with multiple option values.
    #
    # Example:
    # Size = Medium
    # Color = Red
    #
    # options = [Medium, Red]
    options = models.ManyToManyField(
        "ProductOptionValue",
        related_name="variants",
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
    )

    # If price_override is NULL,
    # Product.price will be used.
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    stock = models.PositiveIntegerField(
        default=0,
    )

    image = models.ImageField(
        upload_to="variants/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.title} - {self.sku}"

    @property
    def final_price(self):
        """
        Variant-specific price থাকলে সেটা return করবে।
        না থাকলে Product-এর base price return করবে।
        """

        return (
            self.price_override
            if self.price_override is not None
            else self.product.price
        )


# =========================================================
# Product Image
# =========================================================

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        upload_to="products/gallery/",
    )

    is_feature = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_feature=True),
                name="one_featured_image_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product.title} - Image"