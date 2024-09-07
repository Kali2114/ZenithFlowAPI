"""
Urls mapping for the meditations session app.
"""

from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from meditation_session import views


router = DefaultRouter()
router.register("meditation_sessions", views.MeditationSessionViewSet)
router.register("enrollments", views.EnrollmentViewSet)
router.register("techniques", views.TechniqueViewSet)
router.register("calendar", views.CalendarView, basename="calendar")

app_name = "meditation_session"

urlpatterns = [path("", include(router.urls))]
