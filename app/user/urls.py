"""
Urls mapping for user API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from user import views


app_name = "user"

router = DefaultRouter()
router.register(
    "user/subscriptions", views.SubscriptionViewSet, basename="subscriptions"
)

urlpatterns = [
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("token/", views.CreateTokenView.as_view(), name="token"),
    path("me/", views.ManageUserView.as_view(), name="me"),
    path(
        "user/<int:pk>/profile/",
        views.UserProfileDetailView.as_view(),
        name="userprofile-detail",
    ),
    path(
        "user/<int:pk>/profile/upload-avatar/",
        views.UserProfileDetailView.as_view(),
        name="upload-avatar",
    ),
    path("user/add-funds/", views.AddFundsView.as_view(), name="add-funds"),
    path("", include(router.urls), name="subscriptions"),
]
