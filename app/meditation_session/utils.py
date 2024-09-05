"""
Utils function for app.
"""

from rest_framework.exceptions import PermissionDenied


def check_user_is_instructor(user):
    """Check if the user is an instructor (staff member)."""
    if not user.is_staff:
        raise PermissionDenied(
            "You do not have permission to perform this action."
        )


def check_user_is_creator(user, instance):
    """Check if the user is the creator of the meditation session."""
    if instance.instructor != user:
        raise PermissionDenied(
            "You do not have permission to modify this session."
        )
