from django import forms
from .models import FraudReport

class DeedCheckForm(forms.Form):
    """Public-facing form for the title deed authenticity checker."""
    deed_number = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1234/2020 or DT 1234/2020'}),
    )
    claimed_owner_id = forms.CharField(
        max_length=20, required=False, label="Seller's claimed national ID (optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 63-1234567A12'}),
    )
    claimed_address = forms.CharField(
        max_length=255, required=False, label="Property address as told to you (optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Stand 1234, Borrowdale, Harare'}),
    )

class FraudReportForm(forms.ModelForm):
    class Meta:
        model = FraudReport
        fields = ['related_property', 'title_deed_number', 'description', 'evidence_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'related_property': 'Select the property if it appears in the registry, otherwise leave blank and provide the deed number below.',
            'title_deed_number': 'Required if the property is not in the registry.',
        }