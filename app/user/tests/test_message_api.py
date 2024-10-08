"""
Tests for message API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Message
from user.serializers import MessageSerializer


MESSAGE_URL = reverse("user:messages-list")


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "testname",
    }
    default_user.update(params)

    return get_user_model().objects.create_user(**default_user)


class PublicMessageApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(MESSAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMessageApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.sender = create_user(
            email="sender@example.com", password="testpass123", name="Sender"
        )
        self.receiver = create_user(
            email="receiver@example.com",
            password="testpass123",
            name="Receiver",
        )
        self.client.force_authenticate(self.sender)

    def test_list_messages_for_user(self):
        """Test retrieving messages for authenticated user."""
        other_user = create_user(
            email="other_user@example.com", name="Other User"
        )
        Message.objects.create(
            sender=self.sender, receiver=self.receiver, content="Hello!"
        )
        Message.objects.create(
            sender=self.receiver, receiver=self.sender, content="Hi!"
        )
        Message.objects.create(
            sender=other_user,
            receiver=self.receiver,
            content="I cannot see it!",
        )

        messages = Message.objects.filter(
            sender=self.sender
        ) | Message.objects.filter(receiver=self.sender)
        messages = messages.order_by("-timestamp")
        res = self.client.get(MESSAGE_URL)

        serializer = MessageSerializer(messages, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_send_message_successful(self):
        """Test sending a message to another user success."""
        payload = {
            "receiver": self.receiver.id,
            "content": "Hello, this is a test message.",
        }
        res = self.client.post(MESSAGE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["sender"], self.sender.id)
        self.assertEqual(res.data["receiver"], self.receiver.id)
        self.assertEqual(res.data["content"], payload["content"])

    def test_send_message_to_self_error(self):
        """Test that sending message to self raises an error."""
        payload = {"receiver": self.sender.id, "content": "Message to myself."}
        res = self.client.post(MESSAGE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
