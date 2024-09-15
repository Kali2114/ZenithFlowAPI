"""
Signals for app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from core.models import UserProfile


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    """Delete user profile when the user is deleted."""
    try:
        instance.userprofile.delete()
    except UserProfile.DoesNotExist:
        pass
