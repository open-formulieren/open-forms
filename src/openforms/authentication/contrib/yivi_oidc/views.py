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
    def _yivi_condiscon_scope(options: YiviOptions) -> str:
        """
        Return the yivi condiscon scope as a Signicat additional parameter.

        To allow end-users to choose which information they want to provide, we need to
        pass the Yivi scopes as condiscon. With condiscons we can create logic like;
        "the user must provide bsn OR kvk information.".

        Signicat has some documentation about how the scope should be shaped:
        https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request.
        Yivi has some documentation about the codiscon format and logic:
        https://irma.app/docs/condiscon/.

        The scopes-to-add are fetched from the plugin options `authentication_options`
        and `additional_attributes_groups`.

        When multiple `authentication_options` are defined, the user can choose which one
        to use. Otherwise, if only one is defined, then that one becomes required. When
        no `authentication_options` are defined we fallback to the pseudo authentication
        option.

        All the `additional_attributes_groups` are optional, meaning that the end-user
        can choose which information they want to provide.
        """

        condiscon_items = []
        yivi_global_config = YiviOpenIDConnectConfig.get_solo()

        # Add authentication scopes
        if len(options["authentication_options"]):
            authentication_condiscon = []
            for option in options["authentication_options"]:
                match option:
                    case AuthAttribute.bsn:
                        bsn_attributes = [".".join(yivi_global_config.bsn_claim)]

                        if yivi_global_config.bsn_loa_claim and len(
                            yivi_global_config.bsn_loa_claim
                        ):
                            bsn_attributes.append(
                                ".".join(yivi_global_config.bsn_loa_claim)
                            )

                        authentication_condiscon.append(bsn_attributes)

                    case AuthAttribute.kvk:
                        kvk_attributes = [".".join(yivi_global_config.kvk_claim)]

                        if yivi_global_config.kvk_loa_claim and len(
                            yivi_global_config.kvk_loa_claim
                        ):
                            kvk_attributes.append(
                                ".".join(yivi_global_config.kvk_loa_claim)
                            )

                        authentication_condiscon.append(kvk_attributes)

                    case AuthAttribute.pseudo:
                        # Leave this empty, to allow "anonymous" authentication
                        authentication_condiscon.append(
                            [".".join(yivi_global_config.pseudo_claim)]
                        )

            condiscon_items.append(authentication_condiscon)
        else:
            # If no authentication options are selected, fallback to the pseudo_claim
            condiscon_items.append([[".".join(yivi_global_config.pseudo_claim)]])

        # Add additional groups, as optional
        attributes_groups = AttributeGroup.objects.filter(
            name__in=options["additional_attributes_groups"]
        ).all()
        for attributes_group in attributes_groups:
            # documentation: https://irma.app/docs/condiscon/#other-features
            condiscon_items.append(
                [
                    attributes_group.attributes,
                    # By adding an "empty" choice, this attribute becomes optional.
                    # The empty choice needs to be placed as last, otherwise it doesn't
                    # work (see https://dashboard.signicat.com/contact-us/tickets/207907)
                    [],
                ]
            )

        # Turn condiscon list into a string, and base64 encode it
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
        defined_scope = deepcopy(self.config_class.get_solo().oidc_rp_scopes_list)

        # Add the yivi authentication and additional scopes
        defined_scope.append(self._yivi_condiscon_scope(self.options))

        extra_params["scope"] = " ".join(defined_scope)
        return extra_params


callback_view = OIDCAuthenticationCallbackView.as_view()
