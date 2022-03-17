from django.urls import path

from .views import AuthenticationLogoutView, PluginListView, SubmissionLogoutView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="authentication-plugin-list"),
    path("session", AuthenticationLogoutView.as_view(), name="logout"),
    path(
        "<uuid:uuid>/session", SubmissionLogoutView.as_view(), name="submission-logout"
    ),
]
