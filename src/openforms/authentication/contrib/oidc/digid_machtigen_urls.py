from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import (
    DigiDMachtigenOIDCAuthenticationCallbackView,
    DigiDMachtigenOIDCAuthenticationRequestView,
)

app_name = "digid_machtigen_oidc"


urlpatterns = [
    path(
        "callback/",
        DigiDMachtigenOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path(
        "authenticate/",
        DigiDMachtigenOIDCAuthenticationRequestView.as_view(),
        name="init",
    ),
] + urlpatterns
