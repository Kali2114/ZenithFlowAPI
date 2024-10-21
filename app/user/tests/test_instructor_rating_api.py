"""
Tests for instructor rating API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from user.serializers import InstructorRatingSerializer
from core.models import (
    MeditationSession,
    Enrollment,
    InstructorRating,
)


INSTRUCTOR_RATING_URL = reverse("user:instructor_ratings-list")


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
    }
    default_user.update(params)

    return get_user_model().objects.create(**default_user)


def create_instructor(**params):
    """Create and return a new instructor."""
    default_instructor = {
        "email": "test1@example.com",
        "password": "testpass123",
        "name": "Test Instructor",
    }
    default_instructor.update(params)

    return get_user_model().objects.create(**default_instructor)


def create_meditation_session(**params):
    """Create and return a meditation session."""
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


def create_enrollment(**params):
    """Create and return an enrollment."""
    return Enrollment.objects.create(**params)


def detail_url(instructor_id, instructor_rating_id):
    """Create and return a detail url for instructor rating."""
    return reverse(
        "user:instructor_ratings_detail",
        args=[instructor_id, instructor_rating_id],
    )


class PublicInstructorRatingApi(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(INSTRUCTOR_RATING_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateInstructorRatingApi(TestCase):
    """Test authenticated user API requests."""

    def setUp(self):
        self.user = create_user()
        self.instructor = create_instructor()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_listing_ratings_given_by_user(self):
        """Test listing all ratings given by the authenticated user."""

        InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="Great instructor!",
        )
        another_instructor = create_instructor(
            email="another_instructor@example.com", name="Another Instructor"
        )
        InstructorRating.objects.create(
            user=self.user,
            instructor=another_instructor,
            rating=4,
            comment="Good instructor.",
        )

        another_user = create_user(
            email="another_user@example.com", name="Another User"
        )
        InstructorRating.objects.create(
            user=another_user,
            instructor=self.instructor,
            rating=3,
            comment="Not bad.",
        )
        res = self.client.get(INSTRUCTOR_RATING_URL, {"filter": "given_by_me"})
        ratings = InstructorRating.objects.filter(user=self.user).order_by(
            "-created_at"
        )
        serializer = InstructorRatingSerializer(ratings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_listing_ratings_for_instructor(self):
        """Test listing all ratings for a given instructor."""
        another_user = create_user(
            email="another_user@example.com", name="Another User"
        )

        InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="Excellent!",
        )
        InstructorRating.objects.create(
            user=another_user,
            instructor=self.instructor,
            rating=4,
            comment="Very good.",
        )

        res = self.client.get(
            INSTRUCTOR_RATING_URL,
            {"instructor_id": self.instructor.id},
        )

        ratings = InstructorRating.objects.filter(
            instructor=self.instructor
        ).order_by("-created_at")
        serializer = InstructorRatingSerializer(ratings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def create_instructor_rating_with_successful_enrollment(self):
        """Test that create a new instructor
        rating by user with enrollment is success."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        create_enrollment(
            user=self.user,
            session=meditation_session,
        )
        res = self.client.post(
            INSTRUCTOR_RATING_URL,
            {
                "instructor": self.instructor.id,
                "rating": 5,
                "comment": "Very good instructor",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        rating = InstructorRating.objects.filter(
            instructor=self.instructor.id, user=self.user
        )
        self.assertTrue(rating.exists())
        self.assertEqual(rating.user, self.user)

    def test_create_instructor_rating_without_enrollment_fails(self):
        """Test that creating an instructor rating without enrollment fails."""
        res = self.client.post(
            INSTRUCTOR_RATING_URL,
            {
                "instructor": self.instructor.id,
                "rating": 4,
                "comment": "Great!",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        rating_exists = InstructorRating.objects.filter(
            instructor=self.instructor.id, user=self.user
        ).exists()
        self.assertFalse(rating_exists)

    def test_create_instructor_rating_with_short_comment_fails(self):
        """Test that creating an instructor
        rating with a short comment fails."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        create_enrollment(
            user=self.user,
            session=meditation_session,
        )
        res = self.client.post(
            INSTRUCTOR_RATING_URL,
            {"instructor": self.instructor.id, "rating": 4, "comment": "Bad"},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        rating_exists = InstructorRating.objects.filter(
            instructor=self.instructor.id, user=self.user
        ).exists()
        self.assertFalse(rating_exists)

    def test_delete_own_instructor_rating_success(self):
        """Test that deleting a user's own instructor rating is successful."""
        instructor_rating = InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        url = detail_url(self.instructor.id, instructor_rating.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        rating_exist = InstructorRating.objects.filter(
            user=self.user, instructor=self.instructor
        ).exists()
        self.assertFalse(rating_exist)

    def test_delete_another_user_instructor_rating_fails(self):
        """Test that deleting a other user's instructor rating is failed."""
        other_user = create_user(
            email="other_user@example.com", name="Other User"
        )
        instructor_rating = InstructorRating.objects.create(
            user=other_user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        url = detail_url(self.instructor.id, instructor_rating.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        rating_exist = InstructorRating.objects.filter(
            user=other_user, instructor=self.instructor
        ).exists()
        self.assertTrue(rating_exist)

    def test_delete_instructor_rating_with_invalid_instructor_id_fails(self):
        """Test that deleting an instructor
        rating with incorrect instructor ID fails."""
        instructor_rating = InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        url = detail_url(7, instructor_rating.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        instructor_rating_exists = InstructorRating.objects.filter(
            user=self.user, instructor=self.instructor
        ).exists()
        self.assertTrue(instructor_rating_exists)

    def test_update_own_instructor_rating_success(self):
        """Test that update a user's own instructor rating is successful."""
        instructor_rating = InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        payload = {"rating": 4, "comment": "Updated comment"}
        url = detail_url(self.instructor.id, instructor_rating.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        instructor_rating.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(instructor_rating, k), v)

    def test_update_another_user_instructor_rating_fails(self):
        """Test that deleting a other user's instructor rating is failed."""
        other_user = create_user(
            email="other_user@example.com", name="Other User"
        )
        instructor_rating = InstructorRating.objects.create(
            user=other_user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        payload = {"rating": 1, "comment": "New comment."}
        url = detail_url(self.instructor.id, instructor_rating.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_instructor_rating_with_invalid_instructor_id_fails(self):
        """Test that updating an instructor
        rating with incorrect instructor ID fails."""
        instructor_rating = InstructorRating.objects.create(
            user=self.user,
            instructor=self.instructor,
            rating=5,
            comment="The best instructor ever!",
        )
        payload = {"rating": 2}
        url = detail_url(7, instructor_rating.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(instructor_rating.rating, 5)
