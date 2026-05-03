from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['related_property', 'listed_price', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }