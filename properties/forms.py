from django import forms

from .models import Property


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title_deed_number', 'stand_number', 'suburb', 'city', 'province',
            'gps_latitude', 'gps_longitude', 'size_sqm', 'property_type',
            'registered_owner', 'registration_date', 'status',
            'market_value_estimate', 'description', 'photo',
        ]
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PropertySearchForm(forms.Form):
    query = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by deed number, stand, suburb, or city',
            'class': 'form-control',
        }),
    )
