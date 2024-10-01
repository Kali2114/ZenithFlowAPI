"""
Utils functions for user app.
"""

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import Subscription


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
