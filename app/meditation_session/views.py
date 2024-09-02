"""
Views for the meditation session APIs.
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from core.models import MeditationSession, Enrollment
from meditation_session import serializers


class MeditationSessionViewSet(viewsets.ModelViewSet):
    """Manage meditation sessions in the database."""

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


class EnrollmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Manage enrollments in the database."""

    serializer_class = serializers.EnrollmentDetailSerializer
    queryset = Enrollment.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve enrollments for the authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by(
            "-enrolled_at"
        )

    def get_serializer_class(self):
        """Return the serializer class based on the action."""
        if self.action == "list":
            return serializers.EnrollmentSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new enrollment."""
        serializer.save(user=self.request.user)
