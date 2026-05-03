from django.contrib import admin

from .models import Profile, AuditLog


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'national_id', 'user_email', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified')
    search_fields = ('full_name', 'national_id', 'user__email')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'entity_type', 'entity_id', 'ip_address')
    list_filter = ('action', 'entity_type')
    search_fields = ('user__email', 'description')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
