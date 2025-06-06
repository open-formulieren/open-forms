import base64
import json
from copy import deepcopy
from typing import override

from django.http import HttpRequest
from django.http.response import HttpResponseRedirect

import structlog

from openforms.authentication.constants import AuthAttribute
from digid_eherkenning.oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCInit as _OIDCInit,
)
from furl import furl
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .config import YiviOptions
from .constants import PLUGIN_ID
from .models import AttributeGroup, YiviOpenIDConnectConfig

logger = structlog.stdlib.get_logger(__name__)

YIVI_MESSAGE_PARAMETER = "_yivi-message"
LOGIN_CANCELLED = "login-cancelled"


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    """
    Relay error messages back to the frontend.

    This custom callback view relays any failures back to the public frontend URL of the
    form by setting the appropriate outage parameter and/or message.
    """

    expect_django_user: bool = False  # do NOT create real Django users

    _redirect_next: str
    _config = YiviOpenIDConnectConfig

    def get(self, request: HttpRequest):
        # grab where the redirect next from the session and store it as a temporary
        # attribute. in the event that the failure url needs to be overridden, we
        # then have the value available even *after* mozilla_django_oidc has flushed
        # the session.
        self._redirect_next = request.session.get(_RETURN_URL_SESSION_KEY, "")
        return super().get(request)

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        """
        Return a tuple of the parameter type and the problem code.
        """
        match error, error_description:
            # @TODO set case and change return error_description
            case (
                "access_denied",
                "The user cancelled",
            ):
                return YIVI_MESSAGE_PARAMETER, LOGIN_CANCELLED

            case _:
                return BACKEND_OUTAGE_RESPONSE_PARAMETER, PLUGIN_ID

    @property
    def failure_url(self) -> str:
        """
        On failure, redirect to the form with an appropriate error message.
        """
        # this is expected to be the auth plugin return url, set by the OIDCInit view
        plugin_return_url = furl(
            self._redirect_next or self.get_settings("LOGIN_REDIRECT_URL", "/")
        )
        # this URL is expected to have a ?next query param pointing back to the frontend
        # where the form is rendered/embedded
        _next = plugin_return_url.args["next"]
        assert isinstance(_next, str)
        form_url = furl(_next)

        parameter, problem_code = self.get_error_message_parameters(
            error=self.request.GET.get("error", ""),
            error_description=self.request.GET.get("error_description", ""),
        )
        form_url.args[parameter] = problem_code
        return form_url.url


class OIDCAuthenticationInitView(_OIDCInit):
    options: YiviOptions

    @override
    def get(
        self,
        request: HttpRequest,
        return_url: str = "",
        options: YiviOptions = None,
        *args,
        **kwargs,
    ) -> HttpResponseRedirect:
        self.options = options
        return super().get(request, return_url, *args, **kwargs)

    @staticmethod
    def _yivi_condiscon_scope(options: YiviOptions) -> str:
        """
        Return the yivi condiscon scope as a Signicat additional parameter.

        To allow end-users to choice which information they want to provide, we need to
        pass the Yivi scopes as condiscon. With condiscon's we can create logic like;
        "the user must provide bsn OR kvk information.".

        Signicat has some documentation about how the scope should be shaped:
        https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request.
        Yivi has some documentation about the codiscon format and logic:
        https://irma.app/docs/condiscon/.

        The scopes-to-add are fetched from the plugin options `authentication_options`
        and `additional_attributes_groups`.

        We require the user to choose one of the authentication_options, if multiple are
        defined. Otherwise, if only one is defined, then that one becomes required.
        If no authentication_options are defined, then we don't add an authentication
        scope (this will result into anonymous/pseudo authentication).

        All the additional_attributes_groups are optional, meaning that the end-user can choose
        which information they want to provide.
        """

        condiscon_items = []
        yivi_global_config = YiviOpenIDConnectConfig.get_solo()

        # Add authentication scopes
        if len(options["authentication_options"]):
            authentication_condiscon = []
            for option in options["authentication_options"]:
                if option == AuthAttribute.bsn:
                    authentication_condiscon.append([yivi_global_config.bsn_claim])
                elif option == AuthAttribute.kvk:
                    authentication_condiscon.append(
                        [yivi_global_config.legal_subject_claim]
                    )
            condiscon_items.append(authentication_condiscon)
        else:
            condiscon_items.append([yivi_global_config.pseudo_claim])

        # Add additional groups, as optional
        attributes_groups = AttributeGroup.objects.filter(
            name__in=options["additional_attributes_groups"]
        ).all()
        for attributes_group in attributes_groups:
            # documentation: https://irma.app/docs/condiscon/#other-features
            condiscon_items.append(
                [
                    [],  # The "empty" choice for this additional scope
                    attributes_group["attributes"],
                ]
            )

        # Turn condiscon list into a string, and base64 encode it
        condiscon_string = json.dumps(condiscon_items)

        base64_bytes = base64.b64encode(condiscon_string.encode("ascii"))
        return f"signicat:param:condiscon_base64:{base64_bytes.decode('ascii')}"

    @override
    def get_extra_params(self, request: HttpRequest) -> dict[str, str]:
        """
        Gather extra parameters for the request and add plugin specific authentication
        and additional scopes to the request.
        """
        extra_params = super().get_extra_params(request)
        defined_scope = deepcopy(self.config_class.get_solo().oidc_rp_scopes_list)

        # Add the yivi authentication and additional scopes
        defined_scope.append(self._yivi_condiscon_scope(self.options))

        extra_params["scope"] = " ".join(defined_scope)
        return extra_params


callback_view = OIDCAuthenticationCallbackView.as_view()
