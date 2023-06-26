from django.urls import path

from .views import DigiDAssertionConsumerServiceView, DigiDLoginView

app_name = "digid"


urlpatterns = [
    path("login/", DigiDLoginView.as_view(), name="login"),
    path("acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
