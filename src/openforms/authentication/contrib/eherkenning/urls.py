from django.urls import path

from .views import eHerkenningAssertionConsumerServiceView, eHerkenningLoginView

app_name = "eherkenning"


urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
