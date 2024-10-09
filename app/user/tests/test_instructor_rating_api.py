"""
Tests for instructor rating API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import InstructorRating
from user.serializers import InstructorRatingSerializer


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
            {"filter": "for_instructor", "instructor_id": self.instructor.id},
        )

        ratings = InstructorRating.objects.filter(
            instructor=self.instructor
        ).order_by("-created_at")
        serializer = InstructorRatingSerializer(ratings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
