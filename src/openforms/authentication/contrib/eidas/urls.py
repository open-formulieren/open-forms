from django.urls import path

from digid_eherkenning.views import eHerkenningLoginView

from .views import EIDASAssertionConsumerServiceView

app_name = "eidas"

urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", EIDASAssertionConsumerServiceView.as_view(), name="acs"),
]
