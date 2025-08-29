from django.urls import include, path

from .views import PluginListView, SubmissionLogoutView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="authentication-plugin-list"),
    path(
        "<uuid:uuid>/session", SubmissionLogoutView.as_view(), name="submission-logout"
    ),
]

# add plugin specific URL patterns
urlpatterns += [
    path(
        "plugins/yivi/", include("openforms.authentication.contrib.yivi_oidc.api.urls")
    )
]
