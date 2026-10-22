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

    # Navigation Visibility
    hidden_menus = models.JSONField(
        default=list,
        blank=True,
        help_text='List of admin menu keys to hide from the sidebar'
    )

    # ── Theme & Storefront UI Customizer ──────────────────────────────────────
    store_bg_color = models.CharField(
        max_length=30, default='#fffaf2',
        help_text='Store page background color (e.g. #fffaf2)'
    )
    primary_color = models.CharField(
        max_length=30, default='#ff6b4d',
        help_text='Primary brand & accent color for buttons, badges, links'
    )
    secondary_color = models.CharField(
        max_length=30, default='#f6c64d',
        help_text='Secondary accent color (stars, counter badges)'
    )
    text_color = models.CharField(
        max_length=30, default='#19253b',
        help_text='Primary text / ink color'
    )

    # Header Customization
    HEADER_LAYOUT_CHOICES = [
        ('classic', 'Classic (Logo Left · Nav Center · Icons Right)'),
        ('centered', 'Centered (Logo Center · Clean Editorial Nav)'),
        ('compact', 'Compact Slim (Minimalist Space-Saving Bar)'),
    ]
    header_layout = models.CharField(max_length=20, choices=HEADER_LAYOUT_CHOICES, default='classic')
    header_bg_color = models.CharField(max_length=30, default='#fffaf2')
    header_text_color = models.CharField(max_length=30, default='#19253b')
    header_sticky = models.BooleanField(default=True)
    header_border = models.BooleanField(default=True)
    show_search_in_header = models.BooleanField(default=True)
    show_wishlist_in_header = models.BooleanField(default=True)

    # Announcement Bar
    announcement_enabled = models.BooleanField(default=True)
    announcement_text = models.CharField(
        max_length=255,
        default='Free delivery on orders over ৳1,000 · Designed for curious little humans',
        blank=True
    )
    announcement_bg_color = models.CharField(max_length=30, default='#19253b')
    announcement_text_color = models.CharField(max_length=30, default='#fffaf2')

    # Footer Customization
    FOOTER_LAYOUT_CHOICES = [
        ('classic', '4-Column (Brand Info, Shop Categories, Help/Legal, Newsletter)'),
        ('centered', 'Modern Centered (Centered Logo, Socials, Horizontal Links, Copyright)'),
        ('minimal', 'Compact Minimal (Logo & Copyright Left, Quick Links Right)'),
    ]
    footer_layout = models.CharField(max_length=20, choices=FOOTER_LAYOUT_CHOICES, default='classic')
    footer_bg_color = models.CharField(max_length=30, default='#fffaf2')
    footer_text_color = models.CharField(max_length=30, default='#19253b')

    # Component styling
    card_border_radius = models.CharField(
        max_length=20,
        choices=[
            ('rounded-xl', 'Curved (12px)'),
            ('rounded-2xl', 'Soft Rounded (16px)'),
            ('rounded-3xl', 'Playful Bubble (24px)'),
            ('rounded-lg', 'Standard (8px)'),
        ],
        default='rounded-2xl',
        help_text='Corner roundness for cards, banners and buttons'
    )

    # ── Image Optimization Settings ───────────────────────────────────────────
    img_format = models.CharField(
        max_length=10,
        choices=[
            ('WEBP', 'WebP (Recommended — smallest file size)'),
            ('JPEG', 'JPEG (Wide compatibility)'),
            ('PNG',  'PNG (Lossless, for transparent images)'),
        ],
        default='WEBP',
        help_text='Output format for all uploaded images (product, category, banner, slider)'
    )
    img_quality = models.PositiveSmallIntegerField(
        default=82,
        help_text='Compression quality (1–100). 75–85 = optimal web quality. Lower = smaller file.'
    )
    img_max_width = models.PositiveSmallIntegerField(
        default=1200,
        help_text='Maximum width in pixels for product/banner images (e.g. 1200)'
    )
    img_max_height = models.PositiveSmallIntegerField(
        default=1200,
        help_text='Maximum height in pixels for product/banner images (e.g. 1200)'
    )
    img_thumb_width = models.PositiveSmallIntegerField(
        default=400,
        help_text='Thumbnail max width in pixels (used for category icons, cart thumbnails)'
    )
    img_thumb_height = models.PositiveSmallIntegerField(
        default=400,
        help_text='Thumbnail max height in pixels'
    )
    img_hero_width = models.PositiveSmallIntegerField(
        default=1600,
        help_text='Hero/slider image max width in pixels'
    )
    img_hero_height = models.PositiveSmallIntegerField(
        default=900,
        help_text='Hero/slider image max height in pixels'
    )
    img_lazy_loading = models.BooleanField(
        default=True,
        help_text='Add loading="lazy" to below-the-fold images for faster page display'
    )

    # ── Static Files & CDN Settings ───────────────────────────────────────────
    enable_cdn = models.BooleanField(
        default=False,
        help_text='Enable serving static and media assets via high-speed Content Delivery Network (Cloudflare, BunnyCDN, CloudFront)'
    )
    static_cdn_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='CDN URL prefix for static files (e.g. https://cdn.kidurabd.com/static/)'
    )
    media_cdn_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='CDN URL prefix for media uploads (e.g. https://cdn.kidurabd.com/media/)'
    )
    cloudflare_zone_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Cloudflare Zone ID (found in domain Overview page)'
    )
    cloudflare_api_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Cloudflare API Token with Cache Purge permissions'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return f'Site Settings — {self.site_name}'

    @property
    def card_border_radius_css(self):
        mapping = {
            'rounded-lg': '8px',
            'rounded-xl': '12px',
            'rounded-2xl': '16px',
            'rounded-3xl': '24px',
        }
        return mapping.get(self.card_border_radius, '16px')

    @property
    def hidden_menu_list(self):
        """Returns a list of hidden menu keys safely, handling list, JSON string, or None."""
        val = getattr(self, 'hidden_menus', None)
        if not val:
            return []
        if isinstance(val, list):
            return [str(item).strip() for item in val if item]
        if isinstance(val, str):
            import json
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
            except Exception:
                return [x.strip() for x in val.split(',') if x.strip()]
        return []

    def is_menu_visible(self, menu_key):
        return menu_key not in self.hidden_menu_list

    @classmethod
    def _ensure_table_and_columns(cls):
        """Self-healing helper: ensures custom_admin_sitesettings table, columns, and utf8mb4 charset in MySQL."""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                table_name = cls._meta.db_table
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    from django.core.management import call_command
                    call_command('migrate', 'custom_admin', interactive=False)
                    return

                # Convert entire table to utf8mb4 to support Bengali Unicode characters (৳)
                try:
                    cursor.execute(f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    cursor.execute(f"ALTER TABLE `{table_name}` MODIFY `currency_symbol` VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '৳'")
                except Exception:
                    pass

                cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
                existing_cols = {row[0].lower() for row in cursor.fetchall()}

                if 'maintenance_mode' not in existing_cols:
                    cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `maintenance_mode` tinyint(1) NOT NULL DEFAULT 0")
                if 'maintenance_msg' not in existing_cols:
                    cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `maintenance_msg` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL")
                if 'hidden_menus' not in existing_cols:
                    cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `hidden_menus` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL")

                # Auto-heal Theme settings columns
                theme_cols = {
                    'store_bg_color': "VARCHAR(30) NOT NULL DEFAULT '#fffaf2'",
                    'primary_color': "VARCHAR(30) NOT NULL DEFAULT '#ff6b4d'",
                    'secondary_color': "VARCHAR(30) NOT NULL DEFAULT '#f6c64d'",
                    'text_color': "VARCHAR(30) NOT NULL DEFAULT '#19253b'",
                    'header_layout': "VARCHAR(20) NOT NULL DEFAULT 'classic'",
                    'header_bg_color': "VARCHAR(30) NOT NULL DEFAULT '#fffaf2'",
                    'header_text_color': "VARCHAR(30) NOT NULL DEFAULT '#19253b'",
                    'header_sticky': "TINYINT(1) NOT NULL DEFAULT 1",
                    'header_border': "TINYINT(1) NOT NULL DEFAULT 1",
                    'show_search_in_header': "TINYINT(1) NOT NULL DEFAULT 1",
                    'show_wishlist_in_header': "TINYINT(1) NOT NULL DEFAULT 1",
                    'announcement_enabled': "TINYINT(1) NOT NULL DEFAULT 1",
                    'announcement_text': "VARCHAR(255) NOT NULL DEFAULT 'Free delivery on orders over ৳1,000 · Designed for curious little humans'",
                    'announcement_bg_color': "VARCHAR(30) NOT NULL DEFAULT '#19253b'",
                    'announcement_text_color': "VARCHAR(30) NOT NULL DEFAULT '#fffaf2'",
                    'footer_layout': "VARCHAR(20) NOT NULL DEFAULT 'classic'",
                    'footer_bg_color': "VARCHAR(30) NOT NULL DEFAULT '#fffaf2'",
                    'footer_text_color': "VARCHAR(30) NOT NULL DEFAULT '#19253b'",
                    'card_border_radius': "VARCHAR(20) NOT NULL DEFAULT 'rounded-2xl'",
                }
                for col_name, col_def in theme_cols.items():
                    if col_name not in existing_cols:
                        try:
                            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {col_def}")
                        except Exception:
                            pass

                # Auto-heal Image Optimization settings columns
                img_cols = {
                    'img_format':      "VARCHAR(10) NOT NULL DEFAULT 'WEBP'",
                    'img_quality':     "SMALLINT UNSIGNED NOT NULL DEFAULT 82",
                    'img_max_width':   "SMALLINT UNSIGNED NOT NULL DEFAULT 1200",
                    'img_max_height':  "SMALLINT UNSIGNED NOT NULL DEFAULT 1200",
                    'img_thumb_width': "SMALLINT UNSIGNED NOT NULL DEFAULT 400",
                    'img_thumb_height':"SMALLINT UNSIGNED NOT NULL DEFAULT 400",
                    'img_hero_width':  "SMALLINT UNSIGNED NOT NULL DEFAULT 1600",
                    'img_hero_height': "SMALLINT UNSIGNED NOT NULL DEFAULT 900",
                    'img_lazy_loading':"TINYINT(1) NOT NULL DEFAULT 1",
                }
                for col_name, col_def in img_cols.items():
                    if col_name not in existing_cols:
                        try:
                            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {col_def}")
                        except Exception:
                            pass

                # Auto-heal CDN settings columns
                cdn_cols = {
                    'enable_cdn':           "TINYINT(1) NOT NULL DEFAULT 0",
                    'static_cdn_url':       "VARCHAR(255) NULL",
                    'media_cdn_url':        "VARCHAR(255) NULL",
                    'cloudflare_zone_id':   "VARCHAR(100) NULL",
                    'cloudflare_api_token': "VARCHAR(255) NULL",
                }
                for col_name, col_def in cdn_cols.items():
                    if col_name not in existing_cols:
                        try:
                            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {col_def}")
                        except Exception:
                            pass
        except Exception:
            pass

    def save(self, *args, **kwargs):
        try:
            from products.image_optimizer import compress_and_resize_image
            if self.site_logo:
                compress_and_resize_image(self.site_logo, max_dimensions=(500, 500), quality=85)
            if self.site_favicon:
                compress_and_resize_image(self.site_favicon, max_dimensions=(128, 128), quality=85)
        except Exception:
            pass
        super().save(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('site_settings_singleton')
        except Exception:
            pass

    @classmethod
    def get_settings(cls):
        from django.core.cache import cache
        try:
            cached_obj = cache.get('site_settings_singleton')
            if cached_obj is not None:
                return cached_obj
        except Exception:
            pass

        try:
            obj = cls.objects.first()
            if not obj:
                try:
                    obj, _ = cls.objects.get_or_create(pk=1)
                except Exception:
                    # Likely latin1 charset on table — convert to utf8mb4 and retry
                    cls._ensure_table_and_columns()
                    try:
                        obj, _ = cls.objects.get_or_create(pk=1)
                    except Exception:
                        obj, _ = cls.objects.get_or_create(pk=1, defaults={'currency_symbol': 'Tk'})
            if obj:
                try:
                    cache.set('site_settings_singleton', obj, 3600)
                except Exception:
                    pass
            return obj
        except Exception as first_err:
            import logging
            logging.getLogger('django.request').warning(f"SiteSettings query failed ({first_err}), attempting auto-heal...")
            cls._ensure_table_and_columns()
            try:
                obj = cls.objects.first()
                if not obj:
                    try:
                        obj, _ = cls.objects.get_or_create(pk=1)
                    except Exception:
                        obj, _ = cls.objects.get_or_create(pk=1, defaults={'currency_symbol': 'Tk'})
                if obj:
                    try:
                        cache.set('site_settings_singleton', obj, 3600)
                    except Exception:
                        pass
                return obj
            except Exception as second_err:
                logging.getLogger('django.request').error(f"SiteSettings fallback used: {second_err}")
                return cls(
                    pk=1,
                    site_name='Kidurabd',
                    currency='BDT',
                    currency_symbol='Tk',
                    default_shipping_charge=60,
                    free_shipping_threshold=0,
                    tax_rate=0,
                    maintenance_mode=False,
                    maintenance_msg='We are currently performing maintenance. Please check back soon.',
                )

    @staticmethod
    def _hex_to_rgb(hex_code, default="255 107 77"):
        if not hex_code:
            return default
        h = str(hex_code).lstrip('#').strip()
        if len(h) == 3:
            h = ''.join([c * 2 for c in h])
        if len(h) == 6:
            try:
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                return f"{r} {g} {b}"
            except ValueError:
                pass
        return default

    @property
    def primary_color_rgb(self):
        return self._hex_to_rgb(self.primary_color, "255 107 77")

    @property
    def secondary_color_rgb(self):
        return self._hex_to_rgb(self.secondary_color, "246 198 77")

    @property
    def store_bg_color_rgb(self):
        return self._hex_to_rgb(self.store_bg_color, "255 250 242")

    @property
    def text_color_rgb(self):
        return self._hex_to_rgb(self.text_color, "25 37 59")

    @property
    def logo_url(self):
        try:
            if self.site_logo and hasattr(self.site_logo, 'url'):
                return self.site_logo.url
        except Exception:
            pass
        return None

    @property
    def favicon_url(self):
        try:
            if self.site_favicon and hasattr(self.site_favicon, 'url'):
                return self.site_favicon.url
        except Exception:
            pass
        return None


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
        indexes = [
            models.Index(fields=['is_active', 'sort_order'], name='hero_active_sort_idx'),
        ]

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'[{status}] {self.title}'

    def save(self, *args, **kwargs):
        if self.image:
            from products.image_optimizer import compress_and_resize_image
            compress_and_resize_image(self.image, use_hero=True)  # uses img_hero_width/height from SiteSettings
        super().save(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('home_hero_slides')
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('home_hero_slides')
        except Exception:
            pass


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
        indexes = [
            models.Index(fields=['is_active', 'position'], name='banner_active_pos_idx'),
            models.Index(fields=['is_active', 'position', 'sort_order'], name='banner_act_pos_sort_idx'),
        ]

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'[{status}] {self.title} ({self.get_position_display()})'

    def save(self, *args, **kwargs):
        if self.image:
            from products.image_optimizer import compress_and_resize_image
            compress_and_resize_image(self.image)  # uses img_max_width/height from SiteSettings
        super().save(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('home_banners_dict')
            cache.delete('banner_category_top')
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('home_banners_dict')
            cache.delete('banner_category_top')
        except Exception:
            pass


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
        try:
            actor = request.user if request and getattr(request.user, 'is_authenticated', False) and getattr(request.user, 'pk', None) else None
            ip    = cls._get_ip(request)
            return cls.objects.create(
                actor=actor,
                action=action,
                description=description,
                target_type=target_type,
                target_id=target_id,
                ip_address=ip,
            )
        except Exception:
            return None

    @staticmethod
    def _get_ip(request):
        if not request:
            return None
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            return cf_ip.strip()
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


# ── Page Builder ──────────────────────────────────────────────────────────────

class Page(models.Model):
    """Dynamic pages like Privacy Policy, About Us, Terms & Conditions, etc."""

    title           = models.CharField(max_length=255)
    slug            = models.SlugField(max_length=255, unique=True,
                                       help_text='URL slug, e.g. "privacy-policy" → /page/privacy-policy/')
    content         = models.TextField(blank=True, help_text='Full page HTML content (supports CKEditor rich text).')
    meta_title      = models.CharField(max_length=255, blank=True, help_text='SEO title (defaults to page title if empty).')
    meta_description = models.TextField(blank=True, help_text='SEO meta description.')

    is_published    = models.BooleanField(default=True)
    show_in_footer  = models.BooleanField(default=True, help_text='Show a link to this page in the storefront footer.')
    sort_order      = models.PositiveSmallIntegerField(default=0, help_text='Lower = shown first.')

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['sort_order', 'title']
        verbose_name        = 'Page'
        verbose_name_plural = 'Pages'

    def __str__(self):
        status = '✓' if self.is_published else '✗'
        return f'[{status}] {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete("footer_pages_cache")
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete("footer_pages_cache")
        except Exception:
            pass

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('storefront:page_detail', kwargs={'slug': self.slug})
