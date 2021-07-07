from django.conf.urls import url

from digid_eherkenning.views import eHerkenningLoginView

from .views import eHerkenningAssertionConsumerServiceView

app_name = "eherkenning"

urlpatterns = [
    url(r"login/", eHerkenningLoginView.as_view(), name="login"),
    url(r"acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
