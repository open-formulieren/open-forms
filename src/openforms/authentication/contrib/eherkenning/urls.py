from datetime import datetime, timedelta

from django.core.exceptions import SuspiciousOperation
from django.core.signing import Signer
from django.urls import path

from digid_eherkenning.views import eHerkenningLoginView as _eHerkenningLoginView
from furl import furl

from .views import eHerkenningAssertionConsumerServiceView

app_name = "eherkenning"


class eHerkenningLoginView(_eHerkenningLoginView):
    def get_level_of_assurance(self):
        return_url = furl(self.request.GET.get("next"))
        signed_object = Signer().unsign_object(return_url.args["authn"])
        signature_utc = datetime.fromtimestamp(signed_object["utc"])
        max_age = timedelta(minutes=15)  # same grace period as a Logius SAML request

        if not (
            signed_object["next"] == return_url.args["next"]  # correct form
            and (datetime.utcnow() - signature_utc) < max_age  # recent enough
        ):
            raise SuspiciousOperation("Invalid Level of Assurance signature")

        loa = signed_object["loa"]
        return loa if loa else super().get_level_of_assurance()


urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
