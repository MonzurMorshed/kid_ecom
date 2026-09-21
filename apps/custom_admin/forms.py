from django import forms
from django.contrib.auth import get_user_model

from .models import SiteSettings, PaymentMethod, HeroSlide, Banner, AdminProfile

User = get_user_model()


# ── Shared widget helpers ────────────────────────────────────────────────────
def _input(placeholder='', type_='text'):
    return forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                 'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                 'focus:ring-sky-500 focus:border-transparent transition text-sm',
        'placeholder': placeholder,
    })

def _textarea(placeholder='', rows=3):
    return forms.Textarea(attrs={
        'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                 'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                 'focus:ring-sky-500 focus:border-transparent transition text-sm resize-none',
        'placeholder': placeholder,
        'rows': rows,
    })

def _select():
    return forms.Select(attrs={
        'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                 'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                 'focus:border-transparent transition text-sm',
    })


class AdminRegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CSS, 'placeholder': 'Email Address'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition', 'placeholder': 'Phone Number'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CSS, 'placeholder': 'Password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CSS, 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data


# ── Site Settings Form ───────────────────────────────────────────────────────
class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model  = SiteSettings
        exclude = ['updated_at']
        widgets = {
            'site_name':     _input('e.g. Kidurabd'),
            'site_tagline':  _input('Short tagline for your store'),
            'site_email':    forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                         'focus:ring-sky-500 focus:border-transparent transition text-sm',
                'placeholder': 'contact@example.com',
            }),
            'site_phone':    _input('+880 1XXX-XXXXXX'),
            'site_address':  _textarea('Full store address', rows=2),
            'currency':      _select(),
            'currency_symbol': _input('৳'),
            'free_shipping_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'step': '0.01', 'min': '0',
            }),
            'default_shipping_charge': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'step': '0.01', 'min': '0',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'step': '0.01', 'min': '0', 'max': '100',
            }),
            'facebook_url':  forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                         'focus:ring-sky-500 focus:border-transparent transition text-sm',
                'placeholder': 'https://facebook.com/yourpage',
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                         'focus:ring-sky-500 focus:border-transparent transition text-sm',
                'placeholder': 'https://instagram.com/yourpage',
            }),
            'twitter_url':   forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                         'focus:ring-sky-500 focus:border-transparent transition text-sm',
                'placeholder': 'https://twitter.com/yourpage',
            }),
            'youtube_url':   forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                         'focus:ring-sky-500 focus:border-transparent transition text-sm',
                'placeholder': 'https://youtube.com/yourchannel',
            }),
            'maintenance_msg': _textarea('Maintenance message shown to visitors', rows=3),
        }


# ── Payment Method Form ──────────────────────────────────────────────────────
class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model  = PaymentMethod
        fields = [
            'gateway', 'display_name', 'description', 'icon',
            'is_active', 'sort_order',
            'api_key', 'api_secret', 'sandbox_mode', 'extra_config',
        ]
        widgets = {
            'gateway':      _select(),
            'display_name': _input('e.g. bKash Mobile Banking'),
            'description':  _input('Short description shown at checkout'),
            'sort_order':   forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'min': '0',
            }),
            'api_key':    _input('API Key / Merchant ID'),
            'api_secret': _input('API Secret / Password'),
            'extra_config': _textarea('{"key": "value"}', rows=4),
        }

# ── Hero Slide Form ──────────────────────────────────────────────────────────
class HeroSlideForm(forms.ModelForm):
    class Meta:
        model  = HeroSlide
        fields = [
            'title', 'subtitle', 'image',
            'button_text', 'button_url', 'button_style',
            'text_position', 'overlay_opacity',
            'is_active', 'sort_order',
        ]
        widgets = {
            'title':    _input('e.g. Summer Sale — Up to 50% Off'),
            'subtitle': _input('e.g. Shop the latest kids fashion'),
            'button_text': _input('e.g. Shop Now'),
            'button_url':  _input('/products/ or https://...'),
            'button_style':   _select(),
            'text_position':  _select(),
            'overlay_opacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'min': '0', 'max': '90', 'step': '5',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'min': '0',
            }),
        }


# ── Banner Form ───────────────────────────────────────────────────────────────
class BannerForm(forms.ModelForm):
    class Meta:
        model  = Banner
        fields = [
            'title', 'subtitle', 'image',
            'link_url', 'link_text',
            'position', 'size',
            'badge_text', 'badge_color',
            'is_active', 'sort_order',
            'start_date', 'end_date',
        ]
        widgets = {
            'title':    _input('e.g. New Arrivals — Kids Summer Collection'),
            'subtitle': _input('Optional subtitle shown on the banner'),
            'link_url': _input('/category/summer/ or https://...'),
            'link_text': _input('e.g. Explore Now'),
            'position':    _select(),
            'size':        _select(),
            'badge_text':  _input('e.g. SALE, NEW, 50% OFF'),
            'badge_color': _select(),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'min': '0',
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'type': 'datetime-local',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                         'text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 '
                         'focus:border-transparent transition text-sm',
                'type': 'datetime-local',
            }),
        }

# ── Admin User Edit Form ───────────────────────────────────────────────────────
class AdminEditForm(forms.ModelForm):
    """Edit basic info of an admin user account."""
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                     'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                     'focus:ring-sky-500 focus:border-transparent transition text-sm',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                     'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                     'focus:ring-sky-500 focus:border-transparent transition text-sm',
            'placeholder': 'Last name',
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
                     'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
                     'focus:ring-sky-500 focus:border-transparent transition text-sm',
            'placeholder': 'Email address',
        })
    )
    is_active = forms.BooleanField(required=False)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'is_active']


class AdminProfileForm(forms.ModelForm):
    """Manage role + avatar for an admin user."""
    class Meta:
        model  = AdminProfile
        fields = ['role', 'avatar', 'notes']
        widgets = {
            'role':   _select(),
            'notes':  _textarea('Internal notes (not visible to user)', rows=3),
        }


# ── Change Password Form ─────────────────────────────────────────────────────
_pw_input = lambda ph: forms.PasswordInput(attrs={
    'class': 'w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg '
             'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
             'focus:ring-sky-500 focus:border-transparent transition text-sm',
    'placeholder': ph,
    'autocomplete': 'new-password',
})


class ChangePasswordForm(forms.Form):
    """Change password for any admin user (used by superadmin or self-service)."""
    current_password = forms.CharField(
        label='Current Password',
        required=False,   # Not required when superadmin resets someone else
        widget=_pw_input('Enter current password'),
    )
    new_password = forms.CharField(
        label='New Password',
        min_length=8,
        widget=_pw_input('Minimum 8 characters'),
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=_pw_input('Re-enter new password'),
    )

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('new_password', '')
        cpw = cleaned.get('confirm_password', '')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned
