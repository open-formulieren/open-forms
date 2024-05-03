from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import eHerkenningOIDCAuthenticationCallbackView

app_name = "eherkenning_oidc"


urlpatterns = [
    path(
        "callback/",
        eHerkenningOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
] + urlpatterns
