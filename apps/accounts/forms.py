from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Email address'})
    )
    phone_number = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Phone number (optional)'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Create a password', 'id': 'id_password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Confirm password', 'id': 'id_password_confirm'})
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone and User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone or None

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
        # Use email as username (unique, lowercased)
        email = self.cleaned_data['email'].lower()
        user  = super().save(commit=False)
        user.username    = email
        user.email       = email
        user.is_customer = True
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomerLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Email address', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Password'})
    )
    remember_me = forms.BooleanField(required=False)


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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Your registered email address', 'autofocus': True})
    )


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