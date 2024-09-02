"""
Serializers for meditation session APIs.
"""

from rest_framework import serializers

from core.models import MeditationSession, Enrollment


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
            MeditationSessionSerializer.Meta.read_only_fields + ["instructor"]
        )


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for enrollments."""

    class Meta:
        model = Enrollment
        fields = ["id", "user", "session", "enrolled_at"]
        read_only_fields = ["id", "user", "session", "enrolled_at"]


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for enrollment detail view."""

    session = MeditationSessionDetailSerializer(read_only=True)

    class Meta(EnrollmentSerializer.Meta):
        model = Enrollment
        fields = EnrollmentSerializer.Meta.fields
        read_only_fields = EnrollmentSerializer.Meta.read_only_fields
