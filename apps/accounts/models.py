from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Create your models here.
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_customer = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


# ── UserAddress ───────────────────────────────────────────────────────────────

class UserAddress(models.Model):
    """Multiple saved shipping/billing addresses per customer."""

    ADDRESS_TYPE_CHOICES = [
        ('home',  'Home'),
        ('work',  'Work'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
    )

    # Address type label
    address_type = models.CharField(
        max_length=10,
        choices=ADDRESS_TYPE_CHOICES,
        default='home',
    )

    # Contact details (may differ from account details)
    full_name    = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)

    # Address fields
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100, blank=True)
    postal_code   = models.CharField(max_length=20, blank=True)
    country       = models.CharField(max_length=100, default='Bangladesh')

    # Only one address can be the default per user
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Saved Address'
        verbose_name_plural = 'Saved Addresses'
        ordering            = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.full_name} — {self.address_line1}, {self.city} ({self.get_address_type_display()})'

    def save(self, *args, **kwargs):
        """Ensure only one default address exists per user."""
        if self.is_default:
            # Demote any existing default for this user (excluding self)
            UserAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def formatted(self):
        """Return a single-line formatted address string."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts += [self.city]
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ', '.join(parts)


# ── Wishlist ──────────────────────────────────────────────────────────────────

class Wishlist(models.Model):
    """Persistent server-side wishlist — one row per (user, product) pair."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.product.title}'
