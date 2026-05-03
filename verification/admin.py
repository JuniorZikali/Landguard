from django.contrib import admin
from .models import VerificationRequest, FraudReport

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'queried_deed_number', 'risk_level', 'risk_score', 'authenticity_score', 'request_date')
    list_filter = ('risk_level',)
    search_fields = ('queried_deed_number', 'buyer__email')
    readonly_fields = (
        'buyer', 'related_property', 'queried_deed_number', 'queried_owner_id',
        'queried_address', 'risk_level', 'risk_score', 'authenticity_score',
        'findings', 'report_summary', 'request_date',
    )

@admin.register(FraudReport)
class FraudReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reported_by', 'related_property', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('description', 'title_deed_number')