"""
Tests for calendar API.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import MeditationSession


CALENDAR_URL = reverse("meditation_session:calendar-list")


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "name": "testnname",
        "password": "test123",
    }
    default_user.update(**params)

    return get_user_model().objects.create_user(**default_user)


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return get_user_model().objects.create_superuser(**default_user)


def create_meditation_session(**params):
    """Create and return a new meditation session."""
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


class PublicCalendarApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(CALENDAR_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCalendarApiTests(TestCase):
    """Test authenticated user API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.instructor = create_instructor()
        self.client.force_authenticate(user=self.user)
        self.session1 = create_meditation_session(
            name="Morning Meditation",
            instructor=self.instructor,
            start_time=timezone.now() + timedelta(days=1),
        )
        self.session2 = create_meditation_session(
            name="Evening Meditation",
            instructor=self.instructor,
            start_time=timezone.now() + timedelta(days=2),
        )
        self.session3 = create_meditation_session(
            name="Afternoon Meditation",
            instructor=self.instructor,
            start_time=timezone.now() - timedelta(days=1),
        )
        self.session4 = create_meditation_session(
            name="Simple Meditation",
            instructor=self.instructor,
            start_time=timezone.now() - timedelta(days=2),
        )

    def test_authenticated_user_can_access_past_sessions(self):
        """Test that an authenticated user can access sessions in the past."""
        res = self.client.get(
            CALENDAR_URL, {"end_date": (timezone.now()).date()}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]["name"], self.session3.name)
        self.assertEqual(res.data[1]["name"], self.session4.name)

    def test_retrieve_sessions_for_specific_date(self):
        """Test retrieving sessions for a specific date."""
        date = (timezone.now() + timedelta(days=1)).date()
        res = self.client.get(CALENDAR_URL, {"date": date})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], self.session1.name)

    def test_retrieve_all_sessions(self):
        """Test retrieving all future sessions if no date is provided."""
        res = self.client.get(CALENDAR_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 4)
        self.assertEqual(res.data[0]["name"], self.session2.name)
        self.assertEqual(res.data[1]["name"], self.session1.name)
        self.assertEqual(res.data[2]["name"], self.session3.name)
        self.assertEqual(res.data[3]["name"], self.session4.name)

    def test_retrieve_sessions_in_date_range(self):
        """Test retrieving sessions within a specific date range."""
        start_date = (timezone.now() - timedelta(days=2)).date()
        end_date = (timezone.now() + timedelta(days=1)).date()

        res = self.client.get(
            CALENDAR_URL, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(res.data[0]["name"], self.session1.name)
        self.assertEqual(res.data[1]["name"], self.session3.name)
        self.assertEqual(res.data[2]["name"], self.session4.name)

    def test_no_sessions_in_date_range(self):
        """Test retrieving sessions when none
        exist in the specified date range."""
        start_date = (timezone.now() - timedelta(days=10)).date()
        end_date = (timezone.now() - timedelta(days=8)).date()

        res = self.client.get(
            CALENDAR_URL, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_invalid_date_format(self):
        """Test invalid date format returns 400 bad request."""
        res = self.client.get(CALENDAR_URL, {"start_date": "invalid-date"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_date_after_end_date(self):
        """Test start_date being after end_date returns validation error."""
        start_date = (timezone.now() + timedelta(days=5)).date()
        end_date = (timezone.now() + timedelta(days=1)).date()
        res = self.client.get(
            CALENDAR_URL, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "The start date cannot be after the end date.",
            res.data["non_field_errors"],
        )
