"""
Test for Rating API.
"""

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import (
    MeditationSession,
    Enrollment,
    Rating,
)

from rest_framework import status
from rest_framework.test import APIClient


RATING_URL = reverse("meditation_session:rating-list")


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


def create_meditation_session(is_completed=True, **params):
    """Create and return a new meditation session."""
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
        "is_completed": is_completed,
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


class PublicRatingApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RATING_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRatingApiTests(TestCase):
    """Test authenticated user API requests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_instructor()
        self.user = create_user()
        self.session = create_meditation_session(instructor=self.instructor)
        self.client.force_authenticate(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_list_ratings_for_session(self):
        """Test listing ratings for a session with pagination."""

        Enrollment.objects.create(user=self.user, session=self.session)

        Rating.objects.create(
            user=self.user, session=self.session, rating=4, comment="Good"
        )
        Rating.objects.create(
            user=self.user, session=self.session, rating=5, comment="Great"
        )

        res = self.client.get(RATING_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertEqual(len(res.data["results"]), 2)
        self.assertEqual(res.data["results"][0]["comment"], "Great")
        self.assertEqual(res.data["results"][1]["comment"], "Good")
        self.assertEqual(res.data["results"][0]["rating"], 5)
        self.assertEqual(res.data["results"][1]["rating"], 4)

    def test_create_rating_for_session_success(self):
        """Test create rating for meditation session successful."""

        Enrollment.objects.create(user=self.user, session=self.session)
        payload = {
            "session": self.session.id,
            "rating": 5,
            "comment": "Test Comment",
        }
        res = self.client.post(RATING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["session"], self.session.id)
        self.assertEqual(res.data["rating"], payload["rating"])
        self.assertEqual(res.data["comment"], payload["comment"])
        self.assertEqual(self.session.ratings.count(), 1)

    def test_create_rating_without_enrollment_failed(self):
        """Test create rating for meditation
        session without enrollment fails."""
        payload = {
            "session": self.session.id,
            "rating": 5,
            "comment": "Test Comment",
        }
        res = self.client.post(RATING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_multiple_ratings_to_same_session(self):
        """Test that user cannot add multiple ratings to the same session."""

        Rating.objects.create(
            user=self.user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        payload = {
            "session": self.session.id,
            "rating": 4,
            "comment": "Trying to rate again!",
        }
        res = self.client.post(RATING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.session.ratings.count(), 1)

    def test_cannot_rate_ongoing_session(self):
        """Test that a user cannot rate a session that is still ongoing."""

        ongoing_session = create_meditation_session(
            instructor=self.instructor, is_completed=False
        )
        Enrollment.objects.create(user=self.user, session=ongoing_session)
        payload = {
            "session": ongoing_session.id,
            "rating": 4,
            "comment": "Trying to rate an ongoing session",
        }
        res = self.client.post(RATING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class InstructorRatingApiTests(TestCase):
    """Test authenticated instructor API requests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_instructor()
        self.session = create_meditation_session(instructor=self.instructor)
        self.client.force_authenticate(user=self.instructor)
        self.enrollment = Enrollment.objects.create(
            user=self.instructor, session=self.session
        )

    def test_instructor_cannot_rate_own_session(self):
        """Test that the instructor cannot rate their own session."""

        payload = {
            "session": self.session.id,
            "rating": 5,
            "comment": "Trying to rate my own session!",
        }
        res = self.client.post(RATING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
