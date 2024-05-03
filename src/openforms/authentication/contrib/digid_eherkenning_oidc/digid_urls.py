from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import DigiDOIDCAuthenticationCallbackView

app_name = "digid_oidc"


urlpatterns = [
    path(
        "callback/",
        DigiDOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
] + urlpatterns
