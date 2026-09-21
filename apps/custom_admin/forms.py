from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

INPUT_CSS = 'w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition'

class AdminRegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': INPUT_CSS, 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CSS, 'placeholder': 'Email Address'})
    )
    phone_number = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': INPUT_CSS, 'placeholder': 'Phone Number'})
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


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CSS, 'placeholder': 'Current password'})
    )
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CSS, 'placeholder': 'New password (min 8 chars)'})
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CSS, 'placeholder': 'Confirm new password'})
    )

    def clean_new_password(self):
        pwd = self.cleaned_data.get('new_password', '')
        if len(pwd) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return pwd

    def clean(self):
        cleaned_data = super().clean()
        new = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if new and confirm and new != confirm:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned_data
