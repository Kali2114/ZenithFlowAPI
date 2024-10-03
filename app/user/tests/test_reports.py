"""
Test for instructors reports.
"""

from django.contrib.auth import get_user_model
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Subscription


REPORT_URL = reverse("user:pdf-report")


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return get_user_model().objects.create_superuser(**default_user)


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "testname",
    }
    default_user.update(params)

    return get_user_model().objects.create_user(**default_user)


def create_subscription(user):
    """Create and return a subscription for user."""
    return Subscription.objects.create(
        user=user,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        is_active=True,
        cost=200,
    )


class PublicReportTests(TestCase):
    """Test unauthenticated report requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that auth is required to generate report."""
        res = self.client.get(REPORT_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UserReportTests(TestCase):
    """Tests for authenticated users."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_generate_report_by_user_fails(self):
        """Test that generate a report by user is failed"""
        res = self.client.get(REPORT_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class InstructorReportTests(TestCase):
    """Test for authenticated instructors."""

    def setUp(self):
        self.instructor = create_instructor()
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.instructor)
        self.subscription = create_subscription(self.user)

    def test_generate_report_by_instructor(self):
        """Test that generating report by instructor is successful."""
        create_user(name="Simple", email="Simple@example.com")
        create_user(name="Elephant", email="Elephant@example.com")
        res = self.client.get(REPORT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "application/pdf")
