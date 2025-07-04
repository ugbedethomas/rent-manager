from django import forms
from .models import Tenant, RentAgreement

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['full_name', 'phone_number', 'flat_number', 'flat_type', 'block']

class RentAgreementForm(forms.ModelForm):
    class Meta:
        model = RentAgreement
        fields = ['date_of_agreement', 'date_of_expiration', 'rent_amount', 'payment_or_renewal_note']
