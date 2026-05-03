from django.contrib.auth.models import User
from django.db import models
from properties.models import Property

class VerificationRequest(models.Model):
    """A buyer's request to verify a property before purchase. Objective 3."""
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'), ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'), ('UNKNOWN', 'Unknown / Not in Registry'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    related_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_requests')
    queried_deed_number = models.CharField(max_length=50, help_text="Deed number the buyer typed in")
    queried_owner_id = models.CharField(max_length=20, blank=True, help_text="Optional national ID the seller claims to have")
    queried_address = models.CharField(max_length=255, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='UNKNOWN')
    risk_score = models.IntegerField(default=0)
    authenticity_score = models.IntegerField(default=0)
    findings = models.JSONField(default=list, blank=True)
    report_summary = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Verification by {self.buyer} on {self.queried_deed_number}"
    
    @property
    def risk_badge_class(self):
        return {'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger', 'UNKNOWN': 'secondary'}.get(self.risk_level, 'secondary')


class FraudReport(models.Model):
    """A citizen's report of suspected fraud."""
    STATUS_CHOICES = [
        ('open', 'Open'), ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'), ('dismissed', 'Dismissed'),
    ]
    
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_reports')
    related_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_reports')
    title_deed_number = models.CharField(max_length=50, blank=True, help_text="Deed number, if property is not yet in the registry")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Fraud Report #{self.id} ({self.status})"