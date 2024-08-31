"""
Tests for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful."""
        email = "test@example.com"
        password = "Test123"
        name = "Test_Name"
        user = get_user_model().objects.create_user(
            email=email, password=password, name=name
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@ExAmple.com", "Test2@example.com"],
            ["Test3@example.COM", "Test3@example.com"],
        ]
        for idx, (email, expected) in enumerate(sample_emails):
            user = get_user_model().objects.create_user(
                email=email,
                password="Test123",
                name=f"User{idx}",
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test raises ValueError when creating user without email."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="",
                password="Test123",
                name="Test_Name",
            )

    def test_new_user_without_name_raise_error(self):
        """Test raises ValueError when creating user without email."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="Test@example.com",
                password="Test123",
                name="",
            )

    def test_create_superuser(self):
        """Test creating a superuser successful."""
        user = get_user_model().objects.create_superuser(
            email="example@test.com",
            password="Test123",
            name="Test_Name",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
