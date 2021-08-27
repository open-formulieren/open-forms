from django.conf.urls import url

from mozilla_django_oidc.urls import urlpatterns

from .views import OIDCAuthenticationCallbackView, OIDCAuthenticationRequestView

app_name = "eherkenning_oidc"


urlpatterns = [
    url(
        r"^callback/$",
        OIDCAuthenticationCallbackView.as_view(),
        name="oidc_authentication_callback",
    ),
    url(
        r"^authenticate/$",
        OIDCAuthenticationRequestView.as_view(),
        name="oidc_authentication_init",
    ),
] + urlpatterns
