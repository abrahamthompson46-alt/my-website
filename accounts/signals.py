from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import UserSecurityProfile
from accounts.services.email import get_or_create_security_profile


@receiver(post_save, sender=get_user_model())
def create_security_profile(sender, instance, created, **kwargs):
    if created:
        UserSecurityProfile.objects.get_or_create(user=instance)
