"""
Views for the meditation session APIs.
"""

from django.db import IntegrityError

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from core import models
from meditation_session import serializers
from meditation_session.utils import (
    check_user_is_instructor,
    check_user_is_creator,
)


class MeditationSessionViewSet(viewsets.ModelViewSet):
    """Manage meditation sessions in the database."""

    serializer_class = serializers.MeditationSessionDetailSerializer
    queryset = models.MeditationSession.objects.all().order_by("-id")
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "list":
            return serializers.MeditationSessionSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new meditation session."""
        check_user_is_instructor(self.request.user)
        serializer.save(instructor=self.request.user)

    def perform_update(self, serializer):
        """Update a meditation session only by its creator."""
        instance = self.get_object()
        check_user_is_creator(self.request.user, instance)

        if "instructor" in serializer.validated_data:
            raise ValidationError(
                "You cannot change the instructor of the session."
            )

        serializer.save()

    def perform_destroy(self, instance):
        """Delete a meditation session only by its creator."""
        check_user_is_creator(self.request.user, instance)

        instance.delete()


class EnrollmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Manage enrollments in the database."""

    serializer_class = serializers.EnrollmentDetailSerializer
    queryset = models.Enrollment.objects.all()
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
        session = models.MeditationSession.objects.get(
            id=self.request.data.get("session")
        )
        try:
            serializer.save(user=self.request.user, session=session)
        except IntegrityError:
            raise ValidationError("You are already enrolled in this session.")


class TechniqueViewSet(viewsets.ModelViewSet):
    """Manage techniques in the database."""

    serializer_class = serializers.TechniqueSerializer
    queryset = models.Technique.objects.all().order_by("-name")
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Create a new technique."""
        check_user_is_instructor(self.request.user)
        serializer.save(instructor=self.request.user)

    def perform_update(self, serializer):
        """Update technique only by its creator."""
        instance = self.get_object()
        check_user_is_creator(self.request.user, instance)
        serializer.save()

    def perform_destroy(self, instance):
        """Delete technique only by its creator."""
        check_user_is_creator(self.request.user, instance)
        instance.delete()
