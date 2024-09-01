"""
Tests for meditation session API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import MeditationSession
from meditation_session.serializers import MeditationSessionSerializer


MEDITATION_SESSION_URL = reverse("meditation_session:meditationsession-list")


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "testname",
    }
    default_user.update(params)

    return get_user_model().objects.create_user(**default_user)


def create_meditation_session(**params):
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


class PublicMeditationSessionApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(MEDITATION_SESSION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeditationSessionApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_user()
        self.client.force_authenticate(user=self.instructor)

    def test_retrieve_meditation_sessions(self):
        """Test retrieving a list of meditation sessions."""
        create_meditation_session(instructor=self.instructor)
        create_meditation_session(instructor=self.instructor)
        create_meditation_session(instructor=self.instructor)

        res = self.client.get(MEDITATION_SESSION_URL)
        meditation_sessions = MeditationSession.objects.all().order_by("-id")
        serializer = MeditationSessionSerializer(
            meditation_sessions, many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
