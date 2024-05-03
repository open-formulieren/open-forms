import logging

from furl import furl

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    SoloConfigEHerkenningMixin,
)
from digid_eherkenning_oidc_generics.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
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


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    def get(self, request):
        self._redirect_next = request.session.get("of_redirect_next")
        return super().get(request)

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
        f = furl(self._redirect_next or self.get_settings("LOGIN_REDIRECT_URL", "/"))
        f = furl(f.args["next"])

        parameter, problem_code = self.get_error_message_parameters(
            self.request.GET.get("error", ""),
            self.request.GET.get("error_description", ""),
        )
        f.args[parameter] = problem_code

        return f.url


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
