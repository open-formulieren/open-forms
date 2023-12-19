import logging

from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

import requests
from furl import furl
from mozilla_django_oidc.views import get_next_url

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    SoloConfigEHerkenningMixin,
)
from digid_eherkenning_oidc_generics.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)
from openforms.authentication.contrib.digid.views import (
    DIGID_MESSAGE_PARAMETER,
    LOGIN_CANCELLED,
)
from openforms.authentication.contrib.eherkenning.views import MESSAGE_PARAMETER

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .backends import (
    OIDCAuthenticationDigiDBackend,
    OIDCAuthenticationDigiDMachtigenBackend,
    OIDCAuthenticationEHerkenningBackend,
    OIDCAuthenticationEHerkenningBewindvoeringBackend,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(_OIDCAuthenticationRequestView):
    plugin_identifier = ""

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


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    def get_error_message_parameters(
        self, parameter: str, problem_code: str
    ) -> tuple[str, str]:
        """
        Return a tuple of the parameter type and the problem code.
        """
        return (
            parameter or BACKEND_OUTAGE_RESPONSE_PARAMETER,
            problem_code or self.plugin_identifier,
        )

    @property
    def failure_url(self):
        """
        On failure, redirect to the form with an appropriate error message
        """
        f = furl(self.success_url)
        f = furl(f.args["next"])

        parameter, problem_code = self.get_error_message_parameters(
            self.request.GET.get("error", ""),
            self.request.GET.get("error_description", ""),
        )
        f.args[parameter] = problem_code

        return f.url


class DigiDOIDCAuthenticationRequestView(
    SoloConfigDigiDMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "digid_oidc"


class DigiDOIDCAuthenticationCallbackView(
    SoloConfigDigiDMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "digid_oidc"
    auth_backend_class = OIDCAuthenticationDigiDBackend

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        if error == "access_denied" and error_description == "The user cancelled":
            return (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)

        return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.plugin_identifier)


class eHerkenningOIDCAuthenticationRequestView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "eherkenning_oidc"


class eHerkenningOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "eherkenning_oidc"
    auth_backend_class = OIDCAuthenticationEHerkenningBackend

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        if error == "access_denied" and error_description == "The user cancelled":
            return (
                MESSAGE_PARAMETER % {"plugin_id": self.plugin_identifier.split("_")[0]},
                LOGIN_CANCELLED,
            )

        return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.plugin_identifier)


class DigiDMachtigenOIDCAuthenticationRequestView(
    SoloConfigDigiDMachtigenMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "digid_machtigen_oidc"


class DigiDMachtigenOIDCAuthenticationCallbackView(
    SoloConfigDigiDMachtigenMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "digid_machtigen_oidc"
    auth_backend_class = OIDCAuthenticationDigiDMachtigenBackend

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        if error == "access_denied" and error_description == "The user cancelled":
            return (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)

        return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.plugin_identifier)


class EHerkenningBewindvoeringOIDCAuthenticationRequestView(
    SoloConfigEHerkenningBewindvoeringMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "eherkenning_bewindvoering_oidc"


class EHerkenningBewindvoeringOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningBewindvoeringMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "eherkenning_bewindvoering_oidc"
    auth_backend_class = OIDCAuthenticationEHerkenningBewindvoeringBackend

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        if error == "access_denied" and error_description == "The user cancelled":
            return (
                MESSAGE_PARAMETER % {"plugin_id": self.plugin_identifier.split("_")[0]},
                LOGIN_CANCELLED,
            )

        return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.plugin_identifier)
