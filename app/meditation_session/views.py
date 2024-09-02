"""
Views for the meditation session APIs.
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from core.models import MeditationSession
from meditation_session import serializers


class MeditationSessionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MeditationSessionDetailSerializer
    queryset = MeditationSession.objects.all().order_by("-id")
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "list":
            return serializers.MeditationSessionSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new meditation session."""
        if self.request.user.is_staff:
            serializer.save(instructor=self.request.user)
        else:
            raise PermissionDenied("Only staff members can create sessions.")

    def perform_update(self, serializer):
        """Update a meditation session only by its creator."""
        instance = self.get_object()
        if instance.instructor != self.request.user:
            raise PermissionDenied(
                "You do not have permission to edit this session"
            )

        if "instructor" in serializer.validated_data:
            raise PermissionDenied(
                "You cannot change the instructor of the session"
            )

        serializer.save()

    def perform_destroy(self, instance):
        """Delete a meditation session only by its creator."""
        if instance.instructor != self.request.user:
            raise PermissionDenied(
                "You do not have permission to delete this session"
            )

        instance.delete()
