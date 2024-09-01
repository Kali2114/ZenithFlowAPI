"""
Views for the meditation session APIs.
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import MeditationSession
from meditation_session import serializers


class MeditationSessionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MeditationSessionSerializer
    queryset = MeditationSession.objects.all().order_by("-id")
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
