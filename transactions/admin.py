from django.contrib import admin
from .models import Transaction, RiskFlag

class RiskFlagInline(admin.TabularInline):
    model = RiskFlag
    extra = 0
    readonly_fields = ('flag_type', 'severity', 'description', 'flagged_at')
    can_delete = False

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'related_property', 'seller', 'listed_price', 'risk_level', 'risk_score', 'status', 'listed_at')
    list_filter = ('risk_level', 'status')
    search_fields = ('related_property__title_deed_number', 'seller__email')
    inlines = [RiskFlagInline]
    readonly_fields = ('risk_score', 'risk_level', 'listed_at')

@admin.register(RiskFlag)
class RiskFlagAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'flag_type', 'severity', 'flagged_at')
    list_filter = ('severity', 'flag_type')
    search_fields = ('description', 'transaction__related_property__title_deed_number')