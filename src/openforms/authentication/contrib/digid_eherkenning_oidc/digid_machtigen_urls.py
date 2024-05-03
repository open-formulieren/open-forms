from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import DigiDMachtigenOIDCAuthenticationCallbackView

app_name = "digid_machtigen_oidc"


urlpatterns = [
    path(
        "callback/",
        DigiDMachtigenOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
] + urlpatterns
