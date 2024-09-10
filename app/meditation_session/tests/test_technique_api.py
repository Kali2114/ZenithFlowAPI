"""
Tests for technique API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Technique
from meditation_session.serializers import TechniqueSerializer


TECHNIQUE_URL = reverse("meditation_session:technique-list")


def detail_url(technique_id):
    """Get a detail url for technique."""
    return reverse("meditation_session:technique-detail", args=[technique_id])


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


class PublicTechniqueApiTests(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving techniques."""
        res = self.client.get(TECHNIQUE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTechniqueApiTests(TestCase):
    """Test authenticated user API request."""

    def setUp(self):
        self.user = create_user()
        self.instructor = create_instructor()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_techniques(self):
        """Test retrieving a list of techniques."""
        Technique.objects.create(
            name="Test name",
            description="Test description",
            instructor=self.instructor,
        )
        Technique.objects.create(
            name="Test name 2",
            description="Test description 2",
            instructor=self.instructor,
        )
        res = self.client.get(TECHNIQUE_URL)

        techniques = Technique.objects.all().order_by("-name")
        serializer = TechniqueSerializer(techniques, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_technique_by_user_failed(self):
        """Test creating a technique by user is failed."""
        payload = {"name": "TestName", "description": "Test description"}
        res = self.client.post(TECHNIQUE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_technique_by_user_failed(self):
        """Test updating a technique by user is failed."""
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=self.instructor,
        )
        payload = {"name": "Updatedname"}
        url = detail_url(technique.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        technique.refresh_from_db()
        self.assertEqual(technique.name, "Testname")

    def test_delete_technique_by_user_failed(self):
        """Test deleting a technique by user is failed."""
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=self.instructor,
        )
        url = detail_url(technique.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        technique_exists = Technique.objects.filter(id=technique.id).exists()
        self.assertTrue(technique_exists)


class InstructorTechniqueApiTests(TestCase):
    """Test authenticated instructor API requests."""

    def setUp(self):
        self.instructor = create_instructor()
        self.client = APIClient()
        self.client.force_authenticate(user=self.instructor)

    def test_create_technique_by_instructor_success(self):
        """Creating a new technique by instructor is success."""
        payload = {"name": "test name", "description": "test description"}
        res = self.client.post(TECHNIQUE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        technique = Technique.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(technique, k), v)

    def test_update_own_technique_successful(self):
        """Test updating own technique is successful."""
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=self.instructor,
        )
        payload = {
            "name": "updated name",
            "description": "updated description",
        }
        url = detail_url(technique.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        technique.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(technique, k), v)

    def test_update_other_instructor_technique_failed(self):
        """Test updating other instructor technique is failed."""
        other_instructor = create_instructor(
            email="other_instructor@example.com", name="other_instrctor"
        )
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=other_instructor,
        )
        payload = {
            "name": "updated_name",
            "description": "updated_description",
            "instructor": self.instructor,
        }
        url = detail_url(technique.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        technique.refresh_from_db()
        self.assertEqual(technique.instructor, other_instructor)

    def test_delete_own_technique_successful(self):
        """Test deleting own technique is successful."""
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=self.instructor,
        )
        url = detail_url(technique.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        technique_exists = Technique.objects.filter(id=technique.id).exists()
        self.assertFalse(technique_exists)

    def test_delete_other_instructor_technique_failed(self):
        """Test deleting own technique is successful."""
        other_instructor = create_instructor(
            email="other_instructor@example.com", name="other_instructor"
        )
        technique = Technique.objects.create(
            name="Testname",
            description="testdescription",
            instructor=other_instructor,
        )
        url = detail_url(technique.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        technique_exists = Technique.objects.filter(id=technique.id).exists()
        self.assertTrue(technique_exists)
