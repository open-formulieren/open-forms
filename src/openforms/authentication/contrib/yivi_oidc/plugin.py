from collections.abc import MutableMapping
from typing import Literal, TypedDict, assert_never

from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from openforms.contrib.auth_oidc.plugin import OIDCAuthentication
from openforms.contrib.auth_oidc.typing import OIDCErrors
from openforms.typing import AnyRequest, JSONValue

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
    additional_claims: MutableMapping[str, JSONValue]


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
    ) -> (
        Literal[AuthAttribute.bsn]
        | Literal[AuthAttribute.kvk]
        | Literal[AuthAttribute.pseudo]
    ):
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

        def _build_form_auth(value: str, loa: str) -> FormAuth:
            return {
                "attribute": authentication_attribute,
                "plugin": self.identifier,
                "value": value,
                "loa": loa,
                "additional_claims": normalized_claims.get("additional_claims") or {},
            }

        # Set form authentication values based on the used authentication option
        match authentication_attribute:
            case AuthAttribute.bsn:
                assert "bsn_claim" in normalized_claims
                # Copied from digid_oidc
                return _build_form_auth(
                    normalized_claims["bsn_claim"],
                    str(normalized_claims.get("loa_claim", "")),
                )

            case AuthAttribute.kvk:
                assert "kvk_claim" in normalized_claims
                # Copied from eherkenning_oidc
                return _build_form_auth(
                    normalized_claims["kvk_claim"],
                    str(normalized_claims.get("loa_claim", "")),
                )

            case AuthAttribute.pseudo:
                value = (
                    normalized_claims.get("pseudo_claim", "")
                    or "dummy-set-by@openforms"
                )
                return _build_form_auth(value, "unknown")

            case _:  # pragma: no cover
                assert_never(authentication_attribute)

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
                raise NotImplementedError(
                    f"Auth attribute '{auth_attribute}' is not supported"
                )

        extra_claims = auth_info.additional_claims
        assert isinstance(extra_claims, dict)

        yivi_context: YiviContext = {
            "source": "yivi",
            "authorizee": {
                "legalSubject": {
                    "identifierType": identifier_type,
                    "identifier": auth_info.value,
                    "additionalInformation": extra_claims,
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
