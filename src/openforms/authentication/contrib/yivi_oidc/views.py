import base64
import json
from copy import deepcopy
from typing import override

from django.http import HttpRequest

import structlog
from mozilla_django_oidc_db.views import OIDCInit

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.auth_oidc.views import OIDCAuthenticationCallbackView

from .config import YiviOptions
from .models import AttributeGroup, YiviOpenIDConnectConfig

logger = structlog.stdlib.get_logger(__name__)


class OIDCAuthenticationInitView(OIDCInit):
    options: YiviOptions

    @staticmethod
    def _build_authentication_condiscon(options: YiviOptions) -> list[list[str]]:
        """
        Helper function for creating the "authentication attributes" part of the Signicat
        Yivi condiscon.
        """
        yivi_global_config = YiviOpenIDConnectConfig.get_solo()

        if not len(options["authentication_options"]):
            # If no authentication options are selected, fallback to the pseudo_claim
            return [yivi_global_config.pseudo_claim]

        authentication_condiscon: list[list[str]] = []
        for option in options["authentication_options"]:
            match option:
                case AuthAttribute.bsn:
                    bsn_attributes: list[str] = deepcopy(yivi_global_config.bsn_claim)

                    if yivi_global_config.bsn_loa_claim:
                        bsn_attributes += yivi_global_config.bsn_loa_claim

                    authentication_condiscon.append(bsn_attributes)

                case AuthAttribute.kvk:
                    kvk_attributes: list[str] = deepcopy(yivi_global_config.kvk_claim)

                    if yivi_global_config.kvk_loa_claim:
                        kvk_attributes += yivi_global_config.kvk_loa_claim

                    authentication_condiscon.append(kvk_attributes)

                case AuthAttribute.pseudo:
                    authentication_condiscon.append(yivi_global_config.pseudo_claim)

        return authentication_condiscon

    @staticmethod
    def _build_additional_attributes_condiscon(
        options: YiviOptions,
    ) -> list[list[list[str]]]:
        """
        Helper function for creating the "additional attributes" part of the Signicat
        Yivi condiscon.

        All the `additional_attributes_groups` are optional, meaning that the end-user
        can choose which information they want to provide. This is defined by the empty
        list in the ``additional_attributes_condiscon`` (see below).
        """
        additional_attributes_condiscon: list[list[list[str]]] = []
        attributes_groups = AttributeGroup.objects.filter(
            name__in=options["additional_attributes_groups"]
        )

        for attributes_group in attributes_groups:
            # documentation: https://irma.app/docs/condiscon/#other-features
            additional_attributes_condiscon.append(
                [
                    attributes_group.attributes,
                    # The empty list ensures that this attribute becomes optional.
                    # This needs to be placed as last, otherwise it doesn't work
                    # (see https://dashboard.signicat.com/contact-us/tickets/207907)
                    [],
                ]
            )

        return additional_attributes_condiscon

    def _get_signicat_yivi_condiscon_scope(self, options: YiviOptions) -> str:
        """
        Return the yivi condiscon scope as a Signicat additional parameter.

        To allow end-users to choose which information they want to provide, we need to
        pass the Yivi scopes as condiscon. With condiscons we can create logic like;
        "the user must provide bsn OR kvk information.".

        Signicat has some documentation about how the scope should be shaped:
        https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request.
        Yivi has some documentation about the codiscon format and logic:
        https://irma.app/docs/condiscon/.

        The scopes-to-add are fetched from the plugin options ``authentication_options``
        and ``additional_attributes_groups``.

        When multiple ``authentication_options`` are defined, the user can choose which
        one to use. Otherwise, if only one is defined, then that one becomes required.
        When no ``authentication_options`` are defined we fallback to the pseudo
        authentication option.

        All the `additional_attributes_groups` are optional, meaning that the end-user
        can choose which information they want to provide.
        """

        # Start with condiscon of authentication attributes
        condiscon_items: list[list[list[str]]] = [
            self._build_authentication_condiscon(options)
        ]

        additional_attributes_condiscon: list[list[list[str]]] = (
            self._build_additional_attributes_condiscon(options)
        )
        if additional_attributes_condiscon:
            condiscon_items += additional_attributes_condiscon

        # Turn the condiscon list into a string, and base64 encode it
        condiscon_string = json.dumps(condiscon_items)

        # Create a signicat param scope with the base64 condiscon string.
        # https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request
        base64_bytes = base64.b64encode(condiscon_string.encode("ascii"))
        return f"signicat:param:condiscon_base64:{base64_bytes.decode('ascii')}"

    @override
    def get_extra_params(self, request: HttpRequest) -> dict[str, str]:
        """
        Gather extra parameters for the request and add plugin specific authentication
        and additional scopes to the request.
        """
        extra_params = super().get_extra_params(request)
        defined_scope = deepcopy(self._config.oidc_rp_scopes_list)

        # Add the yivi authentication and additional scopes
        defined_scope.append(self._get_signicat_yivi_condiscon_scope(self.options))

        extra_params["scope"] = " ".join(defined_scope)
        return extra_params


callback_view = OIDCAuthenticationCallbackView.as_view()
