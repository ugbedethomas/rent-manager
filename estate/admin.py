from django.contrib import admin
from .models import Block, Tenant, RentAgreement

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['number']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'flat_number', 'block', 'phone_number', 'flat_type']
    list_filter = ['block', 'flat_type']

@admin.register(RentAgreement)
class RentAgreementAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'date_of_agreement', 'date_of_expiration', 'rent_amount', 'payment_or_renewal_note']
    list_filter = ['date_of_expiration']
