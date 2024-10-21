"""
Utils functions for user app.
"""

from django.utils import timezone
from rest_framework.exceptions import (
    ValidationError,
    PermissionDenied,
)

from core.models import (
    Subscription,
    Enrollment,
)


def check_balance(user, sub_cost):
    """Check that user have enough cash to buy subscription."""
    if user.cash_balance < sub_cost:
        raise ValidationError("Insufficient funds.")


def deduct_user_balance(user, sub_cost):
    """Deduct the cost from the user's balance."""
    user.cash_balance -= sub_cost
    user.save()


def check_expired_subscriptions():
    """Check for expired subscriptions and deactivate them."""
    current_time = timezone.now()
    expired_subscriptions = Subscription.objects.filter(
        end_date__lt=current_time, is_active=True
    )

    for subscription in expired_subscriptions:
        subscription.is_active = False
        subscription.save()


def get_active_subscription(user):
    """Get the active subscription for the user or return None if not found."""
    return user.subscription.filter(is_active=True).first()


def check_user_attended_instructor_session(user, instructor):
    """Check if the given user has attended
    any session conducted by the specified instructor."""
    enrollment = Enrollment.objects.filter(
        user=user,
        session__instructor=instructor,
        session__is_completed=True,
    ).exists()
    if not enrollment:
        raise ValidationError(
            "You must have at last one session with this instructor."
        )


def check_user_can_modify_instructor_rating(instance, user, instructor_id):
    """Check if the user can modify or delete a given instructor rating."""
    if instance.instructor.id != instructor_id:
        raise PermissionDenied("Instructor ID missmatch.")
    if instance.user != user:
        raise PermissionDenied("You can only update your own ratings.")
