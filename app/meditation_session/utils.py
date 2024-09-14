"""
Utils function for app.
"""

from rest_framework.exceptions import PermissionDenied

from core import models


def check_user_is_instructor(user):
    """Check if the user is an instructor (staff member)."""
    if not user.is_staff:
        raise PermissionDenied(
            "You do not have permission to perform this action."
        )


def check_user_is_creator(user, instance):
    """Check if the user is the creator of the instance."""
    if isinstance(instance, models.Rating):
        if instance.user != user:
            raise PermissionDenied(
                "You do not have permission to modify this rating."
            )
    if isinstance(instance, models.MeditationSession):
        if instance.instructor != user:
            raise PermissionDenied(
                "You do not have permission to modify this session."
            )
    elif isinstance(instance, models.Technique):
        if instance.instructor != user:
            raise PermissionDenied(
                "You do not have permission to modify this technique."
            )
