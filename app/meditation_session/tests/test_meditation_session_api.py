"""
Tests for meditation session API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import MeditationSession, Technique
from meditation_session.serializers import (
    MeditationSessionSerializer,
    MeditationSessionDetailSerializer,
)


MEDITATION_SESSION_URL = reverse("meditation_session:meditationsession-list")


def detail_url(meditation_session_id):
    """Get a detail url for meditation session."""
    return reverse(
        "meditation_session:meditationsession-detail",
        args=[meditation_session_id],
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


def create_meditation_session(**params):
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


def add_technique_to_session_url(session_id):
    """Generate URL for adding a technique to a session."""
    return reverse(
        "meditation_session:meditationsession-add-technique", args=[session_id]
    )


def create_technique(**params):
    """Create and return a new technique"""
    default_technique = {
        "name": "Breathing Technique",
        "description": "Arrrgh",
    }
    default_technique.update(**params)
    return Technique.objects.create(**default_technique)


class PublicMeditationSessionApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(MEDITATION_SESSION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeditationSessionApiTests(TestCase):
    """Test authenticated user API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.instructor = create_instructor()

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

    def test_get_meditation_session_detail(self):
        """Test get meditation session detail."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        url = detail_url(meditation_session.id)
        res = self.client.get(url)
        serializer = MeditationSessionDetailSerializer(meditation_session)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_mediation_session_by_user_failed(self):
        """Test creating a mediation session by user failed."""
        payload = {
            "instructor": self.user.id,
            "name": "Mindful Morning",
            "description": "Test description",
            "duration": 40,
            "start_time": timezone.now(),
        }
        res = self.client.post(MEDITATION_SESSION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_meditation_session_by_user_failed(self):
        """Test partial update a meditation session by user failed."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {
            "name": "Updated name",
            "duration": 120,
        }
        url = detail_url(meditation_session.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_meditation_session_by_user_failed(self):
        """Test full update a meditation session by user failed."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {
            "name": "Updated name",
            "description": "Updated Description",
            "duration": 120,
            "status": "planned",
            "max_participants": 100,
            "start_time": timezone.now(),
        }
        url = detail_url(meditation_session.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_meditation_session_instructor_by_user_failed(self):
        """Test update a meditation session instructor by user if failed."""
        another_instructor = create_instructor(
            email="another_instructor@example.com",
            name="Another Instructor",
        )
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {"instructor": another_instructor}
        url = detail_url(meditation_session.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(meditation_session.instructor, self.instructor)

    def test_delete_meditation_session_by_user_failed(self):
        """Test delete a meditation session by user is failed."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        url = detail_url(meditation_session.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        meditation_session_exists = MeditationSession.objects.filter(
            id=meditation_session.id
        ).exists()
        self.assertTrue(meditation_session_exists)

    def test_user_cannot_add_technique_to_meditation_session(self):
        """Test that a regular user cannot add a
        technique to a meditation session."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        technique = create_technique(instructor=self.instructor)
        url = add_technique_to_session_url(session_id=meditation_session.id)
        payload = {"technique_name": technique.name}
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class InstructorMeditationSessionApiTests(TestCase):
    """Test authenticated instructor API requests."""

    def setUp(self):
        self.instructor = create_instructor()
        self.client = APIClient()
        self.client.force_authenticate(user=self.instructor)

    def test_create_meditation_session_by_instructor_successful(self):
        """Test creating a meditation session by instructor is successful."""
        payload = {
            "name": "Mindful Morning",
            "description": "Test description",
            "duration": 40,
            "start_time": timezone.now(),
        }
        res = self.client.post(MEDITATION_SESSION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        meditation_session = MeditationSession.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(meditation_session, k), v)
        self.assertEqual(meditation_session.instructor, self.instructor)

    def test_partial_update_own_meditation_session_successful(self):
        """Test partial update of own meditation session by
        instructor is successful."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {
            "name": "Updated name",
            "duration": 120,
        }
        url = detail_url(meditation_session.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meditation_session.refresh_from_db()
        self.assertEqual(meditation_session.name, payload["name"])
        self.assertEqual(meditation_session.duration, payload["duration"])
        self.assertEqual(meditation_session.instructor, self.instructor)

    def test_partial_update_other_instructors_session_failed(self):
        """Test partial update of another instructor's
        meditation session failed."""
        another_instructor = create_instructor(
            email="another_instructor@example.com",
            name="anothe_instructor",
        )
        meditation_session = create_meditation_session(
            instructor=another_instructor
        )
        payload = {
            "name": "Updated name",
            "duration": 120,
        }
        url = detail_url(meditation_session.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_own_meditation_session_successful(self):
        """Test full update of own meditation session is successful."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {
            "name": "Updated name",
            "description": "Updated Description",
            "duration": 120,
            "status": "planned",
            "max_participants": 100,
            "start_time": timezone.now(),
        }
        url = detail_url(meditation_session.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meditation_session.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(meditation_session, k), v)
        self.assertEqual(meditation_session.instructor, self.instructor)

    def test_full_update_other_instructor_meditation_session_failed(self):
        """Test full update other instructor meditation session is failed."""
        another_instructor = create_instructor(
            email="another_instructor@example.com",
            name="another_instructor",
        )
        meditation_session = create_meditation_session(
            instructor=another_instructor
        )
        payload = {
            "name": "Updated name",
            "description": "Updated Description",
            "duration": 120,
            "status": "planned",
            "max_participants": 100,
            "start_time": timezone.now(),
        }
        url = detail_url(meditation_session.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_meditation_session_instructor_failed(self):
        """Test update meditation session instructor failed."""
        another_instructor = create_instructor(
            email="another_instructor@example.com",
            name="Another Instructor",
        )
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        payload = {"instructor": another_instructor.id}
        url = detail_url(meditation_session.id)
        self.client.patch(url, payload)

        self.assertEqual(meditation_session.instructor, self.instructor)

    def test_delete_own_meditation_session_successful(self):
        """Test delete of own meditation session is successful."""
        meditation_session = create_meditation_session(
            instructor=self.instructor
        )
        url = detail_url(meditation_session.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        meditation_session_exists = MeditationSession.objects.filter(
            id=meditation_session.id
        ).exists()
        self.assertFalse(meditation_session_exists)

    def test_delete_other_instructor_meditation_session_failed(self):
        """Test delete other instructor meditation session failed."""
        another_instructor = create_instructor(
            email="another_instructor@example.com",
            name="another_instructor",
        )
        meditation_session = create_meditation_session(
            instructor=another_instructor
        )
        url = detail_url(meditation_session.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        meditation_session_exists = MeditationSession.objects.filter(
            id=meditation_session.id
        ).exists()
        self.assertTrue(meditation_session_exists)

    def test_add_technique_to_own_meditation_session_success(self):
        """Test adding a new technique to own meditation session success."""
        session = create_meditation_session(instructor=self.instructor)
        technique = create_technique(instructor=self.instructor)
        url = add_technique_to_session_url(session_id=session.id)
        payload = {"technique_name": technique.name}
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertIn(technique, session.techniques.all())

    def test_add_other_instructor_technique_to_session_success(self):
        """Test adding a technique created by
        another instructor to own session is successful."""
        other_instructor = create_instructor(
            email="other_instructor@example.com", name="other_instructor"
        )
        technique = create_technique(instructor=other_instructor)
        session = create_meditation_session(instructor=self.instructor)

        url = add_technique_to_session_url(session_id=session.id)
        payload = {"technique_name": technique.name}
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertIn(technique, session.techniques.all())

    def test_add_technique_to_another_instructors_session_failed(self):
        """Test that adding a technique
         to another instructor's session fails."""
        other_instructor = create_instructor(
            email="other_instructor@example.com", name="other_insructor"
        )
        session = create_meditation_session(instructor=other_instructor)
        technique = create_technique(instructor=self.instructor)
        url = add_technique_to_session_url(session_id=session.id)
        payload = {"technique_name": technique.name}
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_non_existent_technique_to_session_failed(self):
        """Test adding a non-existent technique to a session fails."""
        session = create_meditation_session(instructor=self.instructor)

        url = add_technique_to_session_url(session_id=session.id)
        payload = {"technique_name": ""}  # Empty or non-existent technique
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", res.data)
        self.assertEqual(res.data["detail"], "Technique not found.")
