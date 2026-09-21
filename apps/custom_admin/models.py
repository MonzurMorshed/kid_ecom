from django.conf import settings
from django.db import models


class SiteSettings(models.Model):
    """Singleton model — always use pk=1 via get_settings()."""

    # General
    site_name        = models.CharField(max_length=100, default='Kidurabd')
    site_tagline     = models.CharField(max_length=200, blank=True)
    site_email       = models.EmailField(blank=True)
    site_phone       = models.CharField(max_length=30, blank=True)
    site_address     = models.TextField(blank=True)
    site_logo        = models.ImageField(upload_to='settings/', blank=True, null=True)
    site_favicon     = models.ImageField(upload_to='settings/', blank=True, null=True)

    # Currency
    CURRENCY_CHOICES = [
        ('BDT', '৳  Bangladeshi Taka (BDT)'),
        ('USD', '$  US Dollar (USD)'),
        ('EUR', '€  Euro (EUR)'),
        ('GBP', '£  British Pound (GBP)'),
    ]
    currency         = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='BDT')
    currency_symbol  = models.CharField(max_length=10, default='৳')

    # Shipping & Tax
    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Min order for free shipping (0 = always charged)')
    default_shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=60)
    tax_rate                = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Tax percentage (e.g. 5 for 5%)')

    # Social
    facebook_url  = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url   = models.URLField(blank=True)
    youtube_url   = models.URLField(blank=True)

    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_msg  = models.TextField(
        blank=True,
        default='We are currently performing maintenance. Please check back soon.')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return f'Site Settings — {self.site_name}'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class PaymentMethod(models.Model):
    """Configurable payment gateway/method shown at checkout."""

    GATEWAY_CHOICES = [
        ('bkash',      'bKash'),
        ('nagad',      'Nagad'),
        ('rocket',     'Rocket'),
        ('sslcommerz', 'SSLCommerz'),
        ('stripe',     'Stripe'),
        ('paypal',     'PayPal'),
        ('cod',        'Cash on Delivery'),
        ('bank',       'Bank Transfer'),
        ('other',      'Other'),
    ]

    gateway      = models.CharField(max_length=30, choices=GATEWAY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description  = models.CharField(max_length=255, blank=True)
    icon         = models.ImageField(upload_to='payment_icons/', blank=True, null=True)
    is_active    = models.BooleanField(default=False)
    sort_order   = models.PositiveSmallIntegerField(default=0, help_text='Lower = shown first')

    # Credentials
    api_key     = models.CharField(max_length=500, blank=True, help_text='API Key / Merchant ID')
    api_secret  = models.CharField(max_length=500, blank=True, help_text='API Secret / Password')
    sandbox_mode = models.BooleanField(default=True)
    extra_config = models.JSONField(blank=True, null=True,
                                    help_text='Additional gateway-specific JSON config')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['sort_order', 'display_name']
        verbose_name        = 'Payment Method'
        verbose_name_plural = 'Payment Methods'

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'[{status}] {self.display_name}'


# ── Hero Slider ──────────────────────────────────────────────────────────────

class HeroSlide(models.Model):
    """A single slide in the homepage hero slider."""

    title        = models.CharField(max_length=150)
    subtitle     = models.CharField(max_length=255, blank=True)
    image        = models.ImageField(upload_to='slider/', help_text='Recommended: 1920×700px')
    button_text  = models.CharField(max_length=60, blank=True, default='Shop Now')
    button_url   = models.CharField(max_length=500, blank=True, default='/')
    button_style = models.CharField(max_length=20, choices=[
        ('primary',   'Primary (Sky Blue)'),
        ('secondary', 'Secondary (White Outline)'),
        ('dark',      'Dark'),
    ], default='primary')

    # Text positioning
    text_position = models.CharField(max_length=20, choices=[
        ('left',   'Left'),
        ('center', 'Center'),
        ('right',  'Right'),
    ], default='left')

    # Overlay darkness (0–90)
    overlay_opacity = models.PositiveSmallIntegerField(
        default=40,
        help_text='Overlay darkness 0–90 (0 = no overlay, 90 = very dark)')

    is_active  = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0, help_text='Lower = shown first')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['sort_order', 'created_at']
        verbose_name        = 'Hero Slide'
        verbose_name_plural = 'Hero Slides'

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'[{status}] {self.title}'


# ── Banners ──────────────────────────────────────────────────────────────────

class Banner(models.Model):
    """A promotional/custom banner placed across the site."""

    POSITION_CHOICES = [
        ('home_top',       'Homepage — Top (full width)'),
        ('home_mid',       'Homepage — Middle Section'),
        ('home_bottom',    'Homepage — Bottom Section'),
        ('category_top',   'Category Page — Top'),
        ('product_top',    'Product Listing — Top'),
        ('sidebar',        'Sidebar Widget'),
        ('popup',          'Popup Banner'),
    ]

    SIZE_CHOICES = [
        ('full',  'Full Width'),
        ('half',  'Half Width (2-column)'),
        ('third', 'One-Third Width (3-column)'),
    ]

    title       = models.CharField(max_length=150)
    subtitle    = models.CharField(max_length=255, blank=True)
    image       = models.ImageField(upload_to='banners/')
    link_url    = models.CharField(max_length=500, blank=True, default='/')
    link_text   = models.CharField(max_length=80, blank=True)

    position    = models.CharField(max_length=30, choices=POSITION_CHOICES, default='home_top')
    size        = models.CharField(max_length=10, choices=SIZE_CHOICES, default='full')

    # Optional badge label (e.g. "NEW", "SALE", "50% OFF")
    badge_text  = models.CharField(max_length=30, blank=True)
    badge_color = models.CharField(max_length=20, choices=[
        ('sky',     'Sky Blue'),
        ('rose',    'Rose / Red'),
        ('emerald', 'Emerald / Green'),
        ('amber',   'Amber / Yellow'),
        ('violet',  'Violet / Purple'),
    ], default='sky', blank=True)

    is_active   = models.BooleanField(default=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    # Schedule (optional)
    start_date = models.DateTimeField(blank=True, null=True, help_text='Leave empty to show immediately')
    end_date   = models.DateTimeField(blank=True, null=True, help_text='Leave empty to show indefinitely')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['position', 'sort_order']
        verbose_name        = 'Banner'
        verbose_name_plural = 'Banners'

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'[{status}] {self.title} ({self.get_position_display()})'


# ── Admin Profile (roles) ─────────────────────────────────────────────────────

class AdminProfile(models.Model):
    """Extends the built-in staff/superuser with a named role."""

    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('manager',    'Manager'),
        ('staff',      'Staff'),
    ]

    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_profile',
    )
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    avatar     = models.ImageField(upload_to='admin_avatars/', blank=True, null=True)
    notes      = models.TextField(blank=True, help_text='Internal notes about this admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @classmethod
    def get_or_create_for(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile


# ── Activity Log ──────────────────────────────────────────────────────────────

class ActivityLog(models.Model):
    """Audit trail of actions performed by admin users."""

    ACTION_CHOICES = [
        ('login',    'Login'),
        ('logout',   'Logout'),
        ('create',   'Create'),
        ('update',   'Update'),
        ('delete',   'Delete'),
        ('toggle',   'Toggle'),
        ('import',   'Import'),
        ('export',   'Export'),
        ('settings', 'Settings Changed'),
        ('password', 'Password Changed'),
        ('other',    'Other'),
    ]

    actor       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs',
    )
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES, default='other')
    target_type = models.CharField(max_length=80, blank=True,
                                   help_text='Model or area affected (e.g. Product, Order)')
    target_id   = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        actor = self.actor.username if self.actor else 'system'
        return f'[{self.action}] {actor}: {self.description[:60]}'

    @classmethod
    def log(cls, request, action, description, target_type='', target_id=None):
        """Convenience method to write a log entry."""
        actor = request.user if request and request.user.is_authenticated else None
        ip    = cls._get_ip(request)
        cls.objects.create(
            actor=actor,
            action=action,
            description=description,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip,
        )

    @staticmethod
    def _get_ip(request):
        if not request:
            return None
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
