from itertools import chain
from typing import TypedDict, cast

from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from glom import Path, glom

from openforms.contrib.auth_oidc.plugin import OIDCAuthentication
from openforms.typing import JSONObject

from ...base import LoginLogo
from ...constants import AuthAttribute, LogoAppearance
from ...models import AuthInfo
from ...registry import register
from ...types import YiviContext
from ...typing import FormAuth
from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .config import YiviOptions, YiviOptionsSerializer
from .constants import LOGIN_CANCELLED, PLUGIN_ID, YIVI_MESSAGE_PARAMETER
from .models import AttributeGroup, YiviOpenIDConnectConfig
from .views import OIDCAuthenticationInitView


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
    session_key = "yivi_oidc"
    config_class = YiviOpenIDConnectConfig
    configuration_options = YiviOptionsSerializer
    manage_auth_context = True

    @property
    def init_view(self):
        def view(request, options: YiviOptions, *args, **kwargs):
            yivi_init = OIDCAuthenticationInitView.as_view(
                config_class=YiviOpenIDConnectConfig,
                allow_next_from_query=False,
                options=options,
            )
            return yivi_init(request, *args, **kwargs)

        return view

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

    def strict_mode(self, request: HttpRequest) -> bool:
        # Yivi cannot be strict, as all its attributes should be optional!
        return False

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                return (YIVI_MESSAGE_PARAMETER, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def transform_claims(
        self, options: YiviOptions, normalized_claims: YiviClaims
    ) -> FormAuth:
        authentication_options = options["authentication_options"]
        authentication_attribute = self._get_user_chosen_authentication_attribute(
            authentication_options, normalized_claims
        )

        form_auth = {
            "attribute": authentication_attribute,
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

        return form_auth

    def auth_info_to_auth_context(self, auth_info: AuthInfo) -> YiviContext:
        auth_attribute = AuthAttribute(auth_info.attribute)
        yivi_context: YiviContext = {
            "source": "yivi",
            "authorizee": {
                "legalSubject": {
                    "identifierType": auth_attribute.value,
                    "identifier": auth_info.value,
                    "additionalInformation": cast(dict, auth_info.additional_claims),
                }
            },
        }
        if auth_attribute is not AuthAttribute.pseudo:
            yivi_context["levelOfAssurance"] = auth_info.loa
        return yivi_context

    def before_process_claims(
        self, config: YiviOpenIDConnectConfig, claims: JSONObject
    ):
        """
        Update the global Yivi config, before processing the claims.

        Yivi supports multiple sets of loa config, which have to be dynamically set to
        the "main" loa config in order for the processing of claims to succeed.
        (Otherwise the "non-main" loa config is ignored, and an error is thrown for the
        missing "main" loa config.)
        """
        has_bsn_claim = bool(glom(claims, Path(*config.bsn_claim), default=False))
        has_kvk_claim = bool(glom(claims, Path(*config.kvk_claim), default=False))

        # Set the "global" loa config based on the used authentication method
        match (has_bsn_claim, has_kvk_claim):
            case True, _:
                config.loa_claim = config.bsn_loa_claim
                config.default_loa = config.bsn_default_loa
                config.loa_value_mapping = config.bsn_loa_value_mapping
            case False, True:
                config.loa_claim = config.kvk_loa_claim
                config.default_loa = config.kvk_default_loa
                config.loa_value_mapping = config.kvk_loa_value_mapping
            case False, False:
                config.loa_claim = [""]
                config.default_loa = None
                config.loa_value_mapping = None

    def extract_additional_claims(
        self, options: YiviOptions, claims: JSONObject
    ) -> JSONObject:
        attributes_to_add = AttributeGroup.objects.filter(
            name__in=options.get("additional_attributes_groups", [])
        ).values_list("attributes", flat=True)

        return {
            attribute: claims[attribute]
            for attribute in list(chain.from_iterable(attributes_to_add))
            if attribute in claims
        }

    def get_label(self):
        return "Yivi"

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/yivi.png")),
            href="https://yivi.app/",
            appearance=LogoAppearance.light,
        )
