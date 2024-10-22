"""
Signals for app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from core.models import (
    UserProfile,
    MeditationSession,
    PanelAdmin,
)


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created."""
    if not instance.is_staff and created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=MeditationSession)
def update_profile_on_session_completion(sender, instance, **kwargs):
    """Update user profile when a session is completed."""
    if instance.is_completed:
        for enrollment in instance.enrollments.all():
            enrollment.user.user_profile.update_sessions_and_time()


@receiver(post_save, sender=User)
def create_panel_admin(sender, instance, created, **kwargs):
    """Create a panel admin when a new instructor is created."""
    if instance.is_staff and created:
        PanelAdmin.objects.create(instructor=instance)
        print("PanelAdmin created for:", instance)
