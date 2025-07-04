from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginLog

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    LoginLog.objects.create(user=user, ip=ip)
