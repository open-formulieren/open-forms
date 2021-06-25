from django.urls import path

from digid_eherkenning.views import DigiDLoginView

from .views import DigiDAssertionConsumerServiceView

app_name = "digid"

urlpatterns = [
    path("login/", DigiDLoginView.as_view(), name="login"),
    path("acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
