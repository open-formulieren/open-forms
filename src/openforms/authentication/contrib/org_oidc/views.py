import logging

from django.contrib import auth
from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

import requests
from furl import furl
from mozilla_django_oidc.views import (
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
    get_next_url,
)

from openforms.authentication.contrib.digid_eherkenning_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
)

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .backends import OIDCAuthenticationBackend
from .mixins import SoloConfigMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(SoloConfigMixin, _OIDCAuthenticationRequestView):
    def get(self, request):
        redirect_field_name = self.get_settings("OIDC_REDIRECT_FIELD_NAME", "next")
        next_url = get_next_url(request, redirect_field_name)
        if not next_url:
            raise DisallowedRedirect

        try:
            # Verify that the identity provider endpoint can be reached
            response = requests.get(self.OIDC_OP_AUTH_ENDPOINT)
            if response.status_code > 400:
                response.raise_for_status()
        except Exception as e:
            logger.exception(
                "authentication exception during 'start_login()' of plugin '%(plugin_id)s'",
                {"plugin_id": self.plugin_identifier},
                exc_info=e,
            )
            # append failure parameter and return to form
            f = furl(next_url)
            failure_url = f.args["next"]

            f = furl(failure_url)
            f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = self.plugin_identifier
            return HttpResponseRedirect(f.url)

        return super().get(request)


class OIDCAuthenticationCallbackView(SoloConfigMixin, _OIDCAuthenticationCallbackView):
    # TODO figure out how we want to reuse the patched OIDCAuthenticationCallbackView from digid_eherkenning (and digid_eherkenning_generics)
    #  or possibly move it to mozilla_oidc_db
    auth_backend_class = OIDCAuthenticationBackend

    def login_success(self):
        # override again because our base class removed the .login()
        auth.login(
            self.request, self.user, backend=OIDCAuthenticationBackend.get_import_path()
        )
        assert self.user.is_authenticated
        return super().login_success()
