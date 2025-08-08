from typing import TypedDict, assert_never, cast

from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from openforms.contrib.auth_oidc.plugin import OIDCAuthentication
from openforms.typing import AnyRequest

from ....contrib.auth_oidc.typing import OIDCErrors
from ...base import LoginLogo
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute, LogoAppearance
from ...models import AuthInfo
from ...registry import register
from ...types import YiviContext
from ...typing import FormAuth
from ..digid.constants import DIGID_DEFAULT_LOA
from ..digid.plugin import loa_order as digid_loa_order
from ..eherkenning.constants import EHERKENNING_DEFAULT_LOA
from ..eherkenning.plugin import loa_order as eherkenning_loa_order
from .config import YiviOptions, YiviOptionsSerializer
from .constants import LOGIN_CANCELLED, PLUGIN_ID, YIVI_MESSAGE_PARAMETER
from .oidc_plugins.constants import OIDC_YIVI_IDENTIFIER


class YiviClaims(TypedDict, total=False):
    """
    Processed Yivi claims structure.

    See :attr:`openforms.authentication.yivi_oidc.models` for the source of this
    structure.

    All attributes are optional, as some attributes are only present when user
    login using certain authentication methods (i.e. only when the user logs in
    using bsn, is the bsn claim available).

    `additional_claims` could contain additional attributes received during login.
    This depends on the used Yivi `AdditionalAttributes` by the form, and which
    attributes the user decided to provide.
    The names of these additional attributes/claims are unpredictable: when defining
    the Yivi `AdditionalAttributes`, the admins can assign any attribute they want
    (as different municipalities probably will use different Yivi attribute-sets).
    The names of these attributes will also be used for the claims, so
    `additional_claims` could contain a claim named
    "irma-demo.gemeente.personalData.fullname".
    """

    # Claims for auth attribute bsn
    bsn_claim: str

    # Claims for auth attribute kvk
    kvk_claim: str

    # Claims for anonymous/pseudo authentication
    pseudo_claim: str

    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: str | int | float

    # Mapping for additionally fetched claims
    additional_claims: dict[str, str]


@register(PLUGIN_ID)
class YiviOIDCAuthentication(OIDCAuthentication[YiviClaims, YiviOptions]):
    verbose_name = _("Yivi via OpenID Connect")
    provides_multiple_auth_attributes = True
    # Yivi can provide a range of auth attributes, based on form config and user choice
    provides_auth = (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo)
    oidc_plugin_identifier = OIDC_YIVI_IDENTIFIER
    configuration_options = YiviOptionsSerializer
    manage_auth_context = True

    @staticmethod
    def _get_user_chosen_authentication_attribute(
        authentication_options: list[AuthAttribute],
        normalized_claims: YiviClaims,
    ) -> AuthAttribute:
        """
        Return the user chosen authentication attribute.
        User chosen authentication attribute is defined based on the provided claims. To
        make sure that the plugin allows the specific authentication attribute, the
        defined authentication_options must contain the presumed authentication
        attribute.
        """

        bsn = bool(normalized_claims.get("bsn_claim"))
        kvk = bool(normalized_claims.get("kvk_claim"))

        if AuthAttribute.bsn in authentication_options and bsn:
            return AuthAttribute.bsn
        elif AuthAttribute.kvk in authentication_options and kvk:
            return AuthAttribute.kvk
        else:
            return AuthAttribute.pseudo

    def get_error_codes(self) -> OIDCErrors:
        return {"access_denied": (YIVI_MESSAGE_PARAMETER, LOGIN_CANCELLED)}

    def transform_claims(
        self, options: YiviOptions, normalized_claims: YiviClaims
    ) -> FormAuth:
        authentication_options = options["authentication_options"]
        authentication_attribute = self._get_user_chosen_authentication_attribute(
            authentication_options, normalized_claims
        )

        form_auth = {
            "attribute": authentication_attribute.value,
            "plugin": self.identifier,
            "additional_claims": normalized_claims.get("additional_claims", {}),
        }

        # Set form authentication values based on the used authentication option
        match authentication_attribute:
            case AuthAttribute.bsn:
                # Copied from digid_oidc
                form_auth["value"] = normalized_claims["bsn_claim"]
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))

            case AuthAttribute.kvk:
                # Copied from eherkenning_oidc
                form_auth["value"] = normalized_claims["kvk_claim"]
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))

            case AuthAttribute.pseudo:
                form_auth["value"] = (
                    normalized_claims.get("pseudo_claim", "")
                    or "dummy-set-by@openforms"
                )
                form_auth["loa"] = "unknown"

        return form_auth

    def auth_info_to_auth_context(self, auth_info: AuthInfo) -> YiviContext:
        auth_attribute = AuthAttribute(auth_info.attribute)
        match auth_attribute:
            case AuthAttribute.bsn:
                identifier_type = "bsn"
            case AuthAttribute.kvk:
                identifier_type = "kvkNummer"
            case AuthAttribute.pseudo:
                identifier_type = "opaque"
            case _:
                assert_never(auth_attribute)

        yivi_context: YiviContext = {
            "source": "yivi",
            "authorizee": {
                "legalSubject": {
                    "identifierType": identifier_type,
                    "identifier": auth_info.value,
                    "additionalInformation": cast(dict, auth_info.additional_claims),
                }
            },
            "levelOfAssurance": auth_info.loa,
        }
        return yivi_context

    def get_label(self):
        return "Yivi"

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/yivi.png")),
            href="https://yivi.app/",
            appearance=LogoAppearance.light,
        )

    def check_requirements(self, request: AnyRequest, options: YiviOptions) -> bool:
        # check LoA requirements
        authenticated_loa = request.session[FORM_AUTH_SESSION_KEY]["loa"]
        authenticated_attribute = request.session[FORM_AUTH_SESSION_KEY]["attribute"]

        match authenticated_attribute:
            case AuthAttribute.pseudo:
                # We don't have a loa for pseudo login
                return True

            case AuthAttribute.kvk:
                required = options["kvk_loa"] or EHERKENNING_DEFAULT_LOA
                return eherkenning_loa_order(
                    authenticated_loa
                ) >= eherkenning_loa_order(required)

            case AuthAttribute.bsn:
                required = options["bsn_loa"] or DIGID_DEFAULT_LOA
                return digid_loa_order(authenticated_loa) >= digid_loa_order(required)

            case _:
                assert_never(authenticated_attribute)
