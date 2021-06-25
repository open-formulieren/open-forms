from django.conf.urls import url

from digid_eherkenning.views import DigiDLoginView

from .views import DigiDAssertionConsumerServiceView

app_name = "digid"

urlpatterns = [
    url(r"login/", DigiDLoginView.as_view(), name="login"),
    url(r"acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
