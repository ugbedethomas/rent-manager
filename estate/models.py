from django.db import models
from django.conf import settings

class Block(models.Model):
    number = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"Block {self.number}"

class Tenant(models.Model):
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    flat_number = models.CharField(max_length=10)
    flat_type = models.CharField(max_length=50)  # E.g., Self-Con, 1 Bed
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='tenants')

    def __str__(self):
        return self.full_name

class RentAgreement(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='agreements')
    date_of_agreement = models.DateField()
    date_of_expiration = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_or_renewal_note = models.CharField(max_length=255, blank=True, null=True)

    def is_expired(self):
        from django.utils import timezone
        return self.date_of_expiration < timezone.now().date()

    def __str__(self):
        return f"{self.tenant.full_name} ({self.date_of_agreement} - {self.date_of_expiration})"
class LoginLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=45)

    def __str__(self):
        return f"{self.user.username} at {self.timestamp}"