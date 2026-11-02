from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import UserAddress

User = get_user_model()

# ── Shared input CSS ─────────────────────────────────────────────────────────
_INPUT = (
    'w-full px-4 py-3 rounded-xl border border-ink/15 bg-white/80 text-ink text-sm '
    'placeholder:text-ink/35 focus:outline-none focus:ring-2 focus:ring-coral/40 '
    'focus:border-coral transition'
)


class CustomerRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Last name (optional)'})
    )
    phone_number = forms.CharField(
        max_length=15, required=True,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Mobile number (e.g. 017xxxxxxxx)'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Email address (optional)'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT + ' pr-10', 'placeholder': 'Create a password', 'id': 'id_password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT + ' pr-10', 'placeholder': 'Confirm password', 'id': 'id_password_confirm'})
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password', 'password_confirm']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        if phone.startswith('+880'):
            phone = phone[3:]
        elif phone.startswith('880'):
            phone = phone[2:]
        if not phone:
            raise forms.ValidationError('Mobile number is required.')
        if not (phone.startswith('01') and len(phone) == 11 and phone.isdigit()):
            raise forms.ValidationError('Please enter a valid 11-digit Bangladeshi mobile number (e.g. 017xxxxxxxx).')
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('This mobile number is already registered. Please log in.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('password', '')
        cpw = cleaned.get('password_confirm', '')
        if pw and cpw and pw != cpw:
            self.add_error('password_confirm', 'Passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return cleaned

    def save(self, commit=True):
        phone = self.cleaned_data['phone_number']
        user  = super().save(commit=False)
        user.username    = phone
        user.phone_number = phone
        user.email       = self.cleaned_data.get('email', '').strip().lower()
        user.is_customer = True
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomerLoginForm(forms.Form):
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Mobile number (e.g. 017xxxxxxxx)', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT + ' pr-10', 'placeholder': 'Password', 'id': 'id_password'})
    )
    remember_me = forms.BooleanField(required=False)

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        if phone.startswith('+880'):
            phone = phone[3:]
        elif phone.startswith('880'):
            phone = phone[2:]
        return phone


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': _INPUT + ' text-center text-2xl tracking-[0.4em] font-mono font-bold',
            'placeholder': '••••••',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'autofocus': True,
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not (len(code) == 6 and code.isdigit()):
            raise forms.ValidationError('Please enter a valid 6-digit OTP code.')
        return code


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Email address'})
    )
    phone_number = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Phone number'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': _INPUT + ' resize-none',
            'placeholder': 'Delivery address',
            'rows': 3,
        })
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email


class CustomerChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Current password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'New password', 'id': 'id_new_password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('new_password', '')
        cpw = cleaned.get('confirm_password', '')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'New passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except forms.ValidationError as e:
                self.add_error('new_password', e)
        return cleaned


class CustomerForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Registered mobile number (e.g. 017xxxxxxxx)', 'autofocus': True})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        if phone.startswith('+880'):
            phone = phone[3:]
        elif phone.startswith('880'):
            phone = phone[2:]
        if not phone:
            raise forms.ValidationError('Mobile number is required.')
        return phone


class CustomerResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'New password', 'id': 'id_new_password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('new_password', '')
        cpw = cleaned.get('confirm_password', '')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except forms.ValidationError as e:
                self.add_error('new_password', e)
        return cleaned


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            'address_type',
            'full_name',
            'phone_number',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'is_default',
        ]
        widgets = {
            'address_type': forms.Select(attrs={
                'class': _INPUT + ' cursor-pointer',
            }),
            'full_name': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Recipient full name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Phone number (e.g. 017xxxxxxxx)',
            }),
            'address_line1': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Street address, house / flat no., road',
            }),
            'address_line2': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Apartment, unit, landmark, area (optional)',
            }),
            'city': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'City / Town',
            }),
            'state': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'District / State / Division (optional)',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Postal / ZIP Code (optional)',
            }),
            'country': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Country',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded-lg border-ink/20 text-coral focus:ring-coral/40 cursor-pointer accent-coral',
            }),
        }