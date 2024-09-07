"""
Serializers for meditation session APIs.
"""

from rest_framework import serializers

from core.models import (
    MeditationSession,
    Enrollment,
    Technique,
)
from rest_framework.exceptions import ValidationError


class MeditationSessionSerializer(serializers.ModelSerializer):
    """Serializer for meditation sessions."""

    class Meta:
        model = MeditationSession
        fields = ["id", "name", "start_time"]
        read_only_fields = ["id"]


class MeditationSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for meditation session detail view."""

    class Meta(MeditationSessionSerializer.Meta):
        fields = MeditationSessionSerializer.Meta.fields + [
            "instructor",
            "description",
            "duration",
            "status",
            "max_participants",
            "created_at",
        ]
        read_only_fields = (
            MeditationSessionSerializer.Meta.read_only_fields
            + ["instructor", "current_participants"]
        )


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for enrollments."""

    class Meta:
        model = Enrollment
        fields = ["id", "user", "session", "enrolled_at"]
        read_only_fields = ["id", "user", "enrolled_at"]


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for enrollment detail view."""

    session = MeditationSessionDetailSerializer(read_only=True)

    class Meta(EnrollmentSerializer.Meta):
        model = Enrollment
        fields = EnrollmentSerializer.Meta.fields
        read_only_fields = EnrollmentSerializer.Meta.read_only_fields

    def validate(self, attrs):
        """Validate participants on session."""
        session_id = self.initial_data.get("session")
        session = MeditationSession.objects.get(id=session_id)
        if session.enrollments.count() >= session.max_participants:
            raise ValidationError("Sorry, this session is fully booked.")

        return attrs


class TechniqueSerializer(serializers.ModelSerializer):
    """Serializer for techniques."""

    class Meta:
        model = Technique
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class CalendarSerializer(serializers.Serializer):
    """Serializer for validating calendar query parameters."""

    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    date = serializers.DateField(
        required=False, allow_null=True
    )  # Dodaj pole dla jednej daty

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        date = attrs.get("date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "The start date cannot be after the end date."
            )

        if date and (start_date or end_date):
            raise serializers.ValidationError(
                "You cannot provide both a date and a "
                "date range (start_date/end_date)."
            )

        return attrs
