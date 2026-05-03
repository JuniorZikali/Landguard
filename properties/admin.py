from django.contrib import admin

from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title_deed_number', 'stand_number', 'suburb', 'city',
        'property_type', 'registered_owner', 'status', 'market_value_estimate',
    )
    list_filter = ('status', 'property_type', 'province', 'city')
    search_fields = ('title_deed_number', 'stand_number', 'suburb', 'city')
    autocomplete_fields = ['registered_owner']
    readonly_fields = ('created_at', 'updated_at')
