from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import (
    AzureADOIDCAuthenticationCallbackView,
    AzureADOIDCAuthenticationRequestView,
)

app_name = "azure_ad_oidc"


urlpatterns = [
    path(
        "callback/",
        AzureADOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path(
        "authenticate/",
        AzureADOIDCAuthenticationRequestView.as_view(),
        name="init",
    ),
] + urlpatterns
