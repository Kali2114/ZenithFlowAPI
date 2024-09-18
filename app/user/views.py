"""
Views for user API.
"""

from rest_framework import (
    generics,
    authentication,
    permissions,
    status,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from user.serializers import (
    UserSerializer,
    UserProfileSerializer,
    AuthTokenSerializer,
    UserAvatarSerializer,
)
from core.models import UserProfile


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """Manage user profiles in the database."""

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve profile for authenticated user."""
        return UserProfile.objects.filter(user=self.request.user).select_related('user')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.request.method == "PATCH" and "avatar" in self.request.data:
            return UserAvatarSerializer
        return self.serializer_class

    def perform_update(self, serializer):
        """Allow users to update only their own profiles."""
        if self.request.user != serializer.instance.user:
            raise PermissionDenied(
                "You do not have permission to edit this profile."
            )
        serializer.save()

    @action(methods=["PATCH"], detail=True, url_path="upload-avatar")
    def upload_avatar(self, request, pk=None):
        """Upload avatar for user."""
        user_profile = self.get_object()
        serializer = self.get_serializer(user_profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
