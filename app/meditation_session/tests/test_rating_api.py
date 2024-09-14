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


def session_rating_url(session_id):
    """Return the URL for session ratings."""
    return reverse("meditation_session:session-rating-list", args=[session_id])


def detail_url(session_id, rating_id):
    """Create and return a detail url for rating."""
    return reverse(
        "meditation_session:rating-detail", args=[session_id, rating_id]
    )


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
        instructor = create_instructor()
        session = create_meditation_session(instructor=instructor)
        url = session_rating_url(session.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRatingApiTests(TestCase):
    """Test authenticated user API requests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_instructor()
        self.user = create_user()
        self.session = create_meditation_session(
            instructor=self.instructor, is_completed=True
        )
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

        url = session_rating_url(self.session.id)
        res = self.client.get(url)

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
            "rating": 5,
            "comment": "Test Comment",
        }
        url = session_rating_url(self.session.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["session"], self.session.id)
        self.assertEqual(res.data["rating"], payload["rating"])
        self.assertEqual(res.data["comment"], payload["comment"])
        self.assertEqual(res.data["user"], self.user.email)
        self.assertEqual(self.session.ratings.count(), 1)

    def test_create_rating_without_enrollment_failed(self):
        """Test create rating for meditation
        session without enrollment fails."""
        payload = {
            "rating": 5,
            "comment": "Test Comment",
        }
        url = session_rating_url(self.session.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_multiple_ratings_to_same_session(self):
        """Test that user cannot add multiple ratings to the same session."""
        Enrollment.objects.create(user=self.user, session=self.session)
        Rating.objects.create(
            user=self.user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        payload = {
            "rating": 4,
            "comment": "Trying to rate again!",
        }
        url = session_rating_url(self.session.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.session.ratings.count(), 1)

    def test_cannot_rate_ongoing_session(self):
        """Test that a user cannot rate a session that is still ongoing."""
        ongoing_session = create_meditation_session(
            instructor=self.instructor, is_completed=False
        )
        Enrollment.objects.create(user=self.user, session=ongoing_session)
        payload = {
            "rating": 4,
            "comment": "Trying to rate an ongoing session",
        }
        url = session_rating_url(ongoing_session.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_own_rating(self):
        """Test update own rating is successful."""
        Enrollment.objects.create(user=self.user, session=self.session)
        rating = Rating.objects.create(
            user=self.user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        payload = {"rating": 2, "comment": "Updated Comment."}
        url = detail_url(self.session.id, rating.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        rating.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(rating, k), v)

    def test_update_another_user_rating_failed(self):
        """Test updating another user's rating fails."""
        another_user = create_user(email="another@example.com", name="another")
        rating = Rating.objects.create(
            user=another_user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        payload = {"rating": 2, "comment": "Updated Comment."}
        url = detail_url(self.session.id, rating.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        rating.refresh_from_db()
        self.assertEqual(rating.user, another_user)
        self.assertEqual(rating.rating, 5)

    def test_delete_own_rating_success(self):
        """Test deleting own rating is successful."""
        rating = Rating.objects.create(
            user=self.user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        url = detail_url(self.session.id, rating.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_another_user_rating_failed(self):
        """Test deleting another user rating is failed."""
        another_user = create_user(email="another@example.com", name="Another")
        rating = Rating.objects.create(
            user=another_user,
            session=self.session,
            rating=5,
            comment="Great session!",
        )
        url = detail_url(self.session.id, rating.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        rating_exists = Rating.objects.filter(id=rating.id).exists()
        self.assertTrue(rating_exists)


class InstructorRatingApiTests(TestCase):
    """Test authenticated instructor API requests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_instructor()
        self.session = create_meditation_session(
            instructor=self.instructor, is_completed=True
        )
        self.client.force_authenticate(user=self.instructor)
        self.enrollment = Enrollment.objects.create(
            user=self.instructor, session=self.session
        )

    def test_instructor_cannot_rate_own_session(self):
        """Test that the instructor cannot rate their own session."""
        payload = {
            "rating": 5,
            "comment": "Trying to rate my own session!",
        }
        url = session_rating_url(self.session.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
