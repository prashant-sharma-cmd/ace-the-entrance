from django import forms
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField as BasePhoneNumberField

from .models import User, UserOnboarding


# ── Per-country format hints shown in the error message ───────────────────────
PHONE_HINTS = {
    '+977': '98XXXXXXXX or 97XXXXXXXX',
    '+91':  '9XXXXXXXXX (10 digits)',
    '+1':   '2XX-XXX-XXXX (10 digits)',
    '+44':  '7XXX XXXXXX (10 digits)',
    '+61':  '4XX XXX XXX (9 digits)',
    '+971': '5X XXX XXXX (9 digits)',
    '+974': '3X/5X XXX XXX (8 digits)',
    '+966': '5X XXX XXXX (9 digits)',
}


class FriendlyPhoneNumberField(BasePhoneNumberField):
    """
    Wraps django-phonenumber-field's PhoneNumberField and replaces the
    generic "Enter a valid phone number" error with a dial-code-aware hint.
    The dial code is injected by SignUpForm.clean() after the full E.164
    value is assembled by the front-end JS.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._submitted_dial = '+977'   # default; overridden in SignUpForm.clean()

    def validate(self, value):
        try:
            super().validate(value)
        except ValidationError:
            hint = PHONE_HINTS.get(self._submitted_dial, 'check your number and try again')
            raise ValidationError(
                f"Invalid phone number for the selected country. "
                f"Expected format: {hint}."
            )


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    phone_number = FriendlyPhoneNumberField(required=False)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return p2

    def clean(self):
        cleaned = super().clean()
        # Pass the dial prefix to FriendlyPhoneNumberField so it can show
        # a country-specific error hint if validation fails.
        raw_phone = self.data.get('phone_number', '')
        if raw_phone and raw_phone.startswith('+'):
            for dial in sorted(PHONE_HINTS.keys(), key=len, reverse=True):
                if raw_phone.startswith(dial):
                    self.fields['phone_number']._submitted_dial = dial
                    break
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class OnboardingForm(forms.ModelForm):
    class Meta:
        model  = UserOnboarding
        fields = [
            'primary_purpose',
            'visit_frequency',
            'how_discovered',
            'newsletter_opt_in',
        ]