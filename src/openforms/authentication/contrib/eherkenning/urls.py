from django.urls import path

from digid_eherkenning.views import (
    eHerkenningLoginView,  # pyright: ignore[reportPrivateImportUsage]
)

from .views import eHerkenningAssertionConsumerServiceView

app_name = "eherkenning"


urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
