from django.contrib.auth.models import User
from django.db import models


class Property(models.Model):
    """A property record in the LandGuard registry."""
    
    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disputed', 'Disputed'),
        ('transferred', 'Transferred'),
        ('flagged', 'Flagged'),
    ]
    
    title_deed_number = models.CharField(
        max_length=50, unique=True, db_index=True,
        help_text="Format e.g. 1234/2020 or DT 1234/2020",
    )
    stand_number = models.CharField(max_length=50)
    suburb = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, default='Harare')
    gps_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    gps_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    size_sqm = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Size in square metres",
    )
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    registered_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='owned_properties',
    )
    registration_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    market_value_estimate = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Estimated value in USD",
    )
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='properties/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'
    
    def __str__(self):
        return f"Stand {self.stand_number}, {self.suburb} ({self.title_deed_number})"
    
    @property
    def full_address(self):
        return f"Stand {self.stand_number}, {self.suburb}, {self.city}, {self.province}"
    
    @property
    def is_transactable(self):
        return self.status == 'active'
