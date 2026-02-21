from django import forms
from phonenumber_field.formfields import PhoneNumberField
from models import User, UserOnboarding

class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.CharField, label="First Name")
    last_name = forms.CharField(widget=forms.CharField, label="Last Name")
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    phone_number = PhoneNumberField(required=False, help_text="Optional — for phone-based login")

    class Meta:
        model = User
        fields = ['firstname', 'lastname', 'username', 'email', 'phone_number']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            raise forms.ValidationError("Passwords don't match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email_verified = False
        if commit:
            user.save()
        return user


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = UserOnboarding
        fields = [
            'primary_purpose',
            'visit_frequency',
            'how_discovered',
        ]
        widgets = {
            'primary_purpose': forms.RadioSelect,
            'visit_frequency': forms.RadioSelect,
            'how_discovered': forms.Select,
        }