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


# ── OTPCode ───────────────────────────────────────────────────────────────────

class OTPCode(models.Model):
    """One-time password codes for phone-based signup and password reset flows."""

    PURPOSE_CHOICES = [
        ('signup', 'Signup'),
        ('reset',  'Password Reset'),
    ]

    phone_number = models.CharField(max_length=15)
    code         = models.CharField(max_length=6)
    purpose      = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    is_used      = models.BooleanField(default=False)

    @classmethod
    def generate_for(cls, phone_number, purpose):
        """Generate a 6-digit OTP, invalidate old ones, return the new OTPCode object."""
        import random
        from django.utils import timezone
        import datetime
        # Opportunistic cleanup of old expired codes
        cls.cleanup()
        # Invalidate previous unused codes for same phone + purpose
        cls.objects.filter(phone_number=phone_number, purpose=purpose, is_used=False).update(is_used=True)
        code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        return cls.objects.create(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )

    @classmethod
    def verify(cls, phone_number, code, purpose):
        """Returns OTPCode if valid (unused and not expired), else None."""
        from django.utils import timezone
        try:
            otp = cls.objects.get(
                phone_number=phone_number,
                code=code,
                purpose=purpose,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            return otp
        except cls.DoesNotExist:
            return None

    @classmethod
    def cleanup(cls):
        """Delete expired OTP codes (called opportunistically)."""
        from django.utils import timezone
        try:
            cls.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass

    def consume(self):
        """Mark this OTP as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'OTP Code'

    def __str__(self):
        return f'OTP({self.phone_number}, {self.purpose}, used={self.is_used})'
