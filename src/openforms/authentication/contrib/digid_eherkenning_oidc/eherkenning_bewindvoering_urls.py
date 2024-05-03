from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import EHerkenningBewindvoeringOIDCAuthenticationCallbackView

app_name = "eherkenning_bewindvoering_oidc"


urlpatterns = [
    path(
        "callback/",
        EHerkenningBewindvoeringOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
] + urlpatterns
