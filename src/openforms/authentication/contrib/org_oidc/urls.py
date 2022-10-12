from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import OIDCAuthenticationCallbackView, OIDCAuthenticationRequestView

app_name = "org-oidc"


urlpatterns = [
    path(
        "callback/",
        OIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path(
        "authenticate/",
        OIDCAuthenticationRequestView.as_view(),
        name="init",
    ),
] + urlpatterns
