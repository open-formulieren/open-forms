from django.urls import path

from .views import AttributeGroupListView, PluginListView, SubmissionLogoutView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="authentication-plugin-list"),
    path(
        "plugins/yivi/attribute-groups",
        AttributeGroupListView.as_view(),
        name="yivi-authentication-plugin-attribute-group-list",
    ),
    path(
        "<uuid:uuid>/session", SubmissionLogoutView.as_view(), name="submission-logout"
    ),
]
