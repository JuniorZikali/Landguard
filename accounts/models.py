from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """Extends Django's built-in User with system-specific fields."""
    
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('registrar', 'Registrar'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    national_id = models.CharField(
        max_length=20, unique=True,
        help_text="Zimbabwe National ID (e.g., 63-1234567A12)",
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    address = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this user's identity has been verified by a registrar.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
    
    @property
    def is_registrar_or_admin(self):
        return self.role in ('registrar', 'admin')


class AuditLog(models.Model):
    """Tracks all sensitive user actions for accountability."""
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        actor = self.user.email if self.user else 'system'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} -> {self.action}"


def log_action(user, action, entity_type='', entity_id=None, description='', request=None):
    """Helper to record audit log entries from anywhere in the codebase."""
    ip = None
    if request is not None:
        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip,
    )
#added lines
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'full_name': instance.get_full_name() or instance.username,
                'national_id': f'TEMP-{instance.pk}',
            }
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()