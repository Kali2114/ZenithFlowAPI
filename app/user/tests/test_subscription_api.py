"""
Test for subscription API.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Subscription
from user.serializers import SubscriptionSerializer
from user.utils import check_expired_subscriptions


SUBSCRIPTION_URL = reverse("user:subscriptions-list")


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "Testpass123",
        "name": "Testname",
        "cash_balance": 500,
    }
    default_user.update(**params)

    return get_user_model().objects.create(**default_user)


def create_subscription(user):
    """Create and return a subscription for user."""
    return Subscription.objects.create(
        user=user,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        is_active=True,
        cost=200,
    )


class PublicApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retrieving subscriptions."""
        url = SUBSCRIPTION_URL
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateApiTests(TestCase):
    """Test authenticated user API request."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_subscriptions(self):
        """Test retrieving a list of subscriptions."""
        create_subscription(self.user)
        res = self.client.get(SUBSCRIPTION_URL)

        subscriptions = Subscription.objects.filter(user=self.user).order_by(
            "start_date"
        )
        serializer = SubscriptionSerializer(subscriptions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_retrieve_subscriptions_listing_to_user(self):
        """Test retrieving only user's own subscriptions."""
        create_subscription(self.user)
        other_user = create_user(
            email="other@example.com", password="Pass123", name="Other User"
        )
        create_subscription(other_user)

        res = self.client.get(SUBSCRIPTION_URL)

        subscriptions = Subscription.objects.filter(user=self.user).order_by(
            "start_date"
        )
        serializer = SubscriptionSerializer(subscriptions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"], serializer.data)

    def test_buy_subscription_success(self):
        """Test that buy a subscription by auth user is successful."""
        initial_balance = self.user.cash_balance
        res = self.client.post(SUBSCRIPTION_URL)
        subscription = Subscription.objects.filter(user=self.user).first()
        expected_balance = Decimal(initial_balance) - subscription.cost

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.cash_balance, expected_balance)
        self.assertEqual(subscription.is_active, True)

    def test_buy_subscription_too_less_money(self):
        """Test that buy a subscription when to less money fails."""
        self.user.cash_balance = 0
        res = self.client.post(SUBSCRIPTION_URL)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        subscription_exists = Subscription.objects.filter(
            user=self.user
        ).exists()
        self.assertFalse(subscription_exists)

    def test_expired_subscription_becomes_inactive(self):
        """Test that expired subscription is marked as inactive."""
        subscription = create_subscription(self.user)
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        check_expired_subscriptions()

        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)

    def test_update_not_allowed(self):
        """Test that updating a subscription is not allowed."""
        create_subscription(self.user)
        payload = {"cost": 300}
        res = self.client.patch(SUBSCRIPTION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """Test that deleting a subscription is not allowed."""
        create_subscription(self.user)
        res = self.client.delete(SUBSCRIPTION_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
