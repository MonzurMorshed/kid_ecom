from django import forms
from .models import ContactMessage, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    # Honeypot field for bot detection
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-sm text-ink outline-none focus:border-coral focus:ring-1 focus:ring-coral transition',
                'placeholder': 'Your full name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-sm text-ink outline-none focus:border-coral focus:ring-1 focus:ring-coral transition',
                'placeholder': 'your.email@example.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-sm text-ink outline-none focus:border-coral focus:ring-1 focus:ring-coral transition',
                'placeholder': '+880 1XXXXXXXXX (optional)',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-sm text-ink outline-none focus:border-coral focus:ring-1 focus:ring-coral transition',
                'placeholder': 'Order query, product question, or feedback',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-sm text-ink outline-none focus:border-coral focus:ring-1 focus:ring-coral transition resize-none',
                'placeholder': 'Tell us how we can help you...',
                'rows': 5,
                'required': True,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('website'):
            # Bot filled honeypot
            raise forms.ValidationError('Spam detected.')
        return cleaned_data
