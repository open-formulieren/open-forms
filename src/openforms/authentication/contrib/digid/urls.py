from datetime import datetime, timedelta

from django.core.exceptions import SuspiciousOperation
from django.core.signing import Signer
from django.urls import path

from digid_eherkenning.views import DigiDLoginView as _DigiDLoginView
from furl import furl

from .views import DigiDAssertionConsumerServiceView

app_name = "digid"


class DigiDLoginView(_DigiDLoginView):
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
    path("login/", DigiDLoginView.as_view(), name="login"),
    path("acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
