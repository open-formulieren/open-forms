from django.urls import path

from .views import PluginListView, SubmissionLogoutView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="authentication-plugin-list"),
    path(
        "<uuid:uuid>/session", SubmissionLogoutView.as_view(), name="submission-logout"
    ),
]
