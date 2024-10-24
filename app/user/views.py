"""
Views for user API.
"""

from reportlab.pdfgen import canvas

from datetime import timedelta

from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import (
    generics,
    authentication,
    permissions,
    status,
    mixins,
    viewsets,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView


from user.serializers import (
    UserSerializer,
    UserProfileSerializer,
    AuthTokenSerializer,
    UserAvatarSerializer,
    SubscriptionSerializer,
    MessageSerializer,
    InstructorRatingSerializer,
    PanelAdminSerializer,
)
from core.models import (
    UserProfile,
    Subscription,
    Message,
    InstructorRating,
    PanelAdmin,
    User,
    Enrollment,
)
from user.utils import (
    check_balance,
    deduct_user_balance,
    get_active_subscription,
    check_user_attended_instructor_session,
    check_user_can_modify_instructor_rating,
)
from meditation_session.utils import check_user_is_instructor


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


class AddFundsView(APIView):
    """View to allow users to add funds to their account."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Add funds to the authenticated user's account."""
        amount = request.data.get("amount")

        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {"detail": "Invalid amount provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid amount provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.cash_balance += amount
        user.save()

        return Response(
            {
                "detail": "Funds added successfully.",
                "new_balance": user.cash_balance,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """Manage user profiles in the database."""

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retrieve profile for authenticated user."""
        return UserProfile.objects.filter(
            user=self.request.user
        ).select_related("user")

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


class SubscriptionViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """Manage subscriptions in the database."""

    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retrieve subscriptions for the authenticated user."""
        return (
            self.queryset.filter(user=self.request.user)
            .select_related("user")
            .order_by("-start_date")
        )

    def perform_create(self, serializer):
        """Create a new subscription or extend an existing one."""
        user = self.request.user
        cost = Subscription._meta.get_field("cost").default
        check_balance(user, cost)
        deduct_user_balance(user, cost)

        active_subscription = get_active_subscription(user)
        if active_subscription:
            active_subscription.end_date += timedelta(days=30)
            active_subscription.save()
            return Response(
                {"detail": "Subscription has been extended successfully."},
            )
        else:
            serializer.save(
                user=user,
                cost=cost,
                end_date=timezone.now() + timedelta(days=30),
                is_active=True,
            )
            return Response(
                {
                    "detail": "Subscription purchased successfully.",
                    "subscription": serializer.data,
                },
            )


class PDFReportView(APIView):
    """View for generating PDF report for instructors."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        check_user_is_instructor(request.user)
        subscriptions = Subscription.objects.all().select_related("user")

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            'inline; filename="subscriptions_report.pdf"'
        )

        p = canvas.Canvas(response)
        p.drawString(100, 800, "Report: Users subscription")

        y_position = 750

        p.drawString(50, y_position, "Username")
        p.drawString(150, y_position, "Start Date")
        p.drawString(250, y_position, "End Date")
        p.drawString(350, y_position, "Cost")
        p.drawString(450, y_position, "Active")

        y_position -= 20

        for sub in subscriptions:
            p.drawString(50, y_position, sub.user.email)
            p.drawString(150, y_position, str(sub.start_date))
            p.drawString(250, y_position, str(sub.end_date))
            p.drawString(350, y_position, f"{sub.cost:.2f} PLN")
            p.drawString(450, y_position, "Yes" if sub.is_active else "No")
            y_position -= 20

            if y_position < 100:
                p.showPage()
                y_position = 750

        p.showPage()
        p.save()

        return response


class MessageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Manage messages in the database."""

    serializer_class = MessageSerializer
    queryset = Message.objects.all().order_by("-timestamp")
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retrieve messages for the authenticated users."""
        user = self.request.user
        return (
            Message.objects.filter(Q(sender=user) | Q(receiver=user))
            .select_related("sender", "receiver")
            .order_by("-timestamp")
        )

    def perform_create(self, serializer):
        """Create a new message with sender set to the request user."""
        if serializer.validated_data["receiver"] == self.request.user:
            raise PermissionDenied("You cannot send a message to yourself.")
        serializer.save(sender=self.request.user)


class InstructorRatingViewSet(viewsets.ModelViewSet):
    """Manage instructor ratings in the database."""

    serializer_class = InstructorRatingSerializer
    queryset = InstructorRating.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the instructor rating
        for the given instructor and rating ID."""
        instructor_id = self.kwargs.get("instructor_id")
        rating_id = self.kwargs.get("pk")
        return get_object_or_404(
            InstructorRating, instructor_id=instructor_id, id=rating_id
        )

    def get_queryset(self):
        """Retrieve ratings depending on the user context."""
        user = self.request.user
        instructor_id = self.request.query_params.get("instructor_id")

        if instructor_id:
            return (
                InstructorRating.objects.filter(instructor=instructor_id)
                .select_related("user", "instructor")
                .order_by("-created_at")
            )
        return InstructorRating.objects.filter(user=user).order_by(
            "-created_at"
        )

    def perform_create(self, serializer):
        """Create a new instructor rating"""
        instructor = serializer.validated_data["instructor"]
        check_user_attended_instructor_session(self.request.user, instructor)
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Update only your own instructor rating."""
        instance = self.get_object()
        instructor_id = kwargs.get("instructor_id")
        check_user_can_modify_instructor_rating(
            instance, request.user, instructor_id
        )
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Destroy only your own instructor rating."""
        instance = self.get_object()
        instructor_id = kwargs.get("instructor_id")
        check_user_can_modify_instructor_rating(
            instance, request.user, instructor_id
        )
        return super().destroy(request, *args, **kwargs)


class PanelAdminView(APIView):
    """View to return panel admin data."""

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, user_id):
        """Return data for admin panel."""
        user = get_object_or_404(
            User.objects.prefetch_related(
                Prefetch(
                    "subscription",
                    queryset=Subscription.objects.filter(is_active=True),
                ),
                Prefetch(
                    "enrollments",
                    queryset=Enrollment.objects.select_related("session"),
                ),
            ),
            id=user_id,
        )
        admin_panel = PanelAdmin.objects.get(instructor=user)
        serializer = PanelAdminSerializer(admin_panel)

        return Response(serializer.data)
