from django.contrib.auth.models import User
from django.db import models

from properties.models import Property


class Transaction(models.Model):
    """A property listing or sale attempt."""
    STATUS_CHOICES = [
        ('listed', 'Listed'), ('pending', 'Pending'), ('under_review', 'Under Review'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('flagged', 'Flagged for Fraud'),
    ]
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'), ('MEDIUM', 'Medium Risk'), ('HIGH', 'High Risk'),
    ]
    
    related_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='transactions')
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales')
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='purchases')
    listed_price = models.DecimalField(max_digits=12, decimal_places=2)
    risk_score = models.IntegerField(default=0, help_text="0–100")
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='LOW')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='listed')
    notes = models.TextField(blank=True)
    listed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-listed_at']
    
    def __str__(self):
        return f"Transaction #{self.id} | {self.related_property} | {self.risk_level}"
    
    @property
    def risk_badge_class(self):
        return {'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger'}.get(self.risk_level, 'secondary')


class RiskFlag(models.Model):
    """A specific red flag raised against a transaction by the risk engine."""
    SEVERITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]
    FLAG_TYPE_CHOICES = [
        ('seller_id_mismatch', 'Seller is not the registered owner'),
        ('duplicate_active_listing', 'Property has another active listing'),
        ('recently_transferred', 'Property was recently transferred'),
        ('price_below_market', 'Listed price suspiciously below market value'),
        ('invalid_deed_number', 'Title deed number is invalid'),
        ('disputed_status', 'Property is currently disputed or flagged'),
        ('incomplete_record', 'Property record is incomplete'),
        ('multiple_listings_same_seller', 'Seller has unusually many recent listings'),
        ('unverified_owner', 'Registered owner identity is unverified'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='risk_flags')
    flag_type = models.CharField(max_length=50, choices=FLAG_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    description = models.TextField()
    flagged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-flagged_at']
    
    def __str__(self):
        return f"{self.get_flag_type_display()} ({self.severity})"
    
    @property
    def severity_badge_class(self):
        return {'LOW': 'info', 'MEDIUM': 'warning', 'HIGH': 'danger'}.get(self.severity, 'secondary')