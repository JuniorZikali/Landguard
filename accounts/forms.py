from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(UserCreationForm):
    """Custom registration form requiring email and Zimbabwe national ID."""
    
    email = forms.EmailField(
        required=True,
        help_text="You'll use this to log in.",
    )
    national_id = forms.CharField(
        max_length=20,
        required=True,
        help_text="Zimbabwe National ID e.g. 63-1234567A12",
    )
    full_name = forms.CharField(max_length=150, required=True)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(
        choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
        required=True,
        help_text="Registrar accounts are created by an administrator.",
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'full_name', 'national_id',
            'phone', 'role', 'password1', 'password2',
        ]
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_national_id(self):
        nid = self.cleaned_data['national_id']
        if Profile.objects.filter(national_id__iexact=nid).exists():
            raise forms.ValidationError(
                "A user with this national ID already exists."
            )
        return nid
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        # Signal already created the Profile — update it with the form values
        Profile.objects.filter(user=user).update(
            full_name=self.cleaned_data['full_name'],
            national_id=self.cleaned_data['national_id'],
            role=self.cleaned_data['role'],
            phone=self.cleaned_data.get('phone', ''),
    )
    # Refresh so user.profile reflects the updated values
        user.refresh_from_db()
        return user

class EmailLoginForm(forms.Form):
    """Login form using email + password instead of username."""
    
    email = forms.EmailField(label='Email', required=True)
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        required=True,
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'address']
