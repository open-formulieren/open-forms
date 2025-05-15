from __future__ import annotations

from typing import ClassVar, NotRequired, Protocol, TypedDict

from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models import BaseConfig
from flags.state import flag_enabled
from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.authentication.constants import LegalSubjectIdentifierType
from openforms.authentication.typing import FormAuth
from openforms.contrib.digid_eherkenning.utils import (
    get_digid_logo,
    get_eherkenning_logo,
)
from openforms.forms.models import Form
from openforms.typing import StrOrPromise
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin, CosignSlice, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
)
from .views import (
    digid_init,
    digid_machtigen_init,
    eherkenning_bewindvoering_init,
    eherkenning_init,
)

OIDC_ID_TOKEN_SESSION_KEY = "oidc_id_token"


def get_config_to_plugin() -> dict[type[BaseConfig], OIDCAuthentication]:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    return {
        plugin.config_class: plugin
        for plugin in register
        if isinstance(plugin, OIDCAuthentication)
    }


class AuthInit(Protocol):
    def __call__(
        self, request: HttpRequest, return_url: str, *args, **kwargs
    ) -> HttpResponseBase: ...


class OptionsT(TypedDict):
    pass


# can't bind T to JSONObject because TypedDict and dict[str, ...] are not considered
# assignable... :(
class OIDCAuthentication[T, OptionsT](BasePlugin[OptionsT]):
    verbose_name: StrOrPromise = ""
    provides_auth: AuthAttribute
    session_key: str = ""
    config_class: ClassVar[type[BaseConfig]]
    init_view: ClassVar[AuthInit]

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: OptionsT
    ):
        return_url_query = {"next": form_url}
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url_query[CO_SIGN_PARAMETER] = co_sign_param

        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query=return_url_query,
        )

        # "evaluate" the view, this achieves two things:
        #
        # * we save a browser redirect cycle since we get the redirect to the identity
        #   provider immediately
        # * we control the config to apply 100% server side rather than passing it as
        #   a query parameter, which prevents a malicious user from messing with the
        #   redirect URL
        #
        # This may raise `OIDCProviderOutage`, which bubbles into the generic auth
        # start_view and gets handled there.
        response = self.init_view(request, return_url=return_url)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        if not (claim := request.session.get(self.session_key)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def transform_claims(self, normalized_claims: T) -> FormAuth:
        raise NotImplementedError("Subclasses must implement 'transform_claims'")

    def handle_return(self, request: HttpRequest, form: Form, options: OptionsT):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: T | None = request.session.get(self.session_key)
        if normalized_claims and CO_SIGN_PARAMETER not in request.GET:
            form_auth = self.transform_claims(normalized_claims)
            request.session[FORM_AUTH_SESSION_KEY] = form_auth

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if id_token := request.session.get(OIDC_ID_TOKEN_SESSION_KEY):
            config = self.config_class.get_solo()
            do_op_logout(config, id_token)

        keys_to_delete = (
            "oidc_login_next",  # from upstream library
            self.session_key,
            _RETURN_URL_SESSION_KEY,
            OIDC_ID_TOKEN_SESSION_KEY,
        )
        for key in keys_to_delete:
            if key in request.session:
                del request.session[key]


class DigiDClaims(TypedDict):
    """
    Processed DigiD claims structure.

    See :attr:`digid_eherkenning.oidc.models.DigiDConfig.CLAIMS_CONFIGURATION` for the
    source of this structure.
    """

    bsn_claim: str
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]


@register("digid_oidc")
class DigiDOIDCAuthentication(OIDCAuthentication[DigiDClaims, OptionsT]):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = "digid_oidc:bsn"
    config_class = OFDigiDConfig
    init_view = staticmethod(digid_init)

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))

    def transform_claims(self, normalized_claims: DigiDClaims) -> FormAuth:
        return {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": normalized_claims["bsn_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
        }


class EHClaims(TypedDict):
    """
    Processed EH claims structure.

    See :attr:`digid_eherkenning.oidc.models.EHerkenningConfig.CLAIMS_CONFIGURATION`
    for the source of this structure.
    """

    identifier_type_claim: NotRequired[str]
    legal_subject_claim: str
    acting_subject_claim: NotRequired[str]
    branch_number_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(OIDCAuthentication[EHClaims, OptionsT]):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    session_key = "eherkenning_oidc:kvk"
    config_class = OFEHerkenningConfig
    init_view = staticmethod(eherkenning_init)

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))

    def transform_claims(self, normalized_claims: EHClaims) -> FormAuth:
        acting_subject_identifier_value = normalized_claims.get(
            "acting_subject_claim", ""
        )
        strict_mode = flag_enabled("DIGID_EHERKENNING_OIDC_STRICT")

        if strict_mode and not acting_subject_identifier_value:
            raise ValueError(
                "The acting_subject_claim value must be set to a non-empty value in "
                "strict mode. You may have to contact your identity provider to ensure "
                "it is present in the OIDC claims."
            )

        form_auth: FormAuth = {
            "plugin": self.identifier,
            # TODO: look at `identifier_type_claim` and return kvk or rsin accordingly.
            # Currently we have no support for RSIN at all, so that will need to be
            # added first (and has implications for prefill!)
            "attribute": self.provides_auth,
            "value": normalized_claims["legal_subject_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
            "acting_subject_identifier_type": "opaque",
            "acting_subject_identifier_value": acting_subject_identifier_value
            or "dummy-set-by@openforms",
        }
        if service_restriction := normalized_claims.get("branch_number_claim", ""):
            form_auth["legal_subject_service_restriction"] = service_restriction
        return form_auth


class DigiDmachtigenClaims(TypedDict):
    """
    Processed DigiD Machtigen claims structure.

    See :attr:`digid_eherkenning.oidc.models.DigiDMachtigenConfig.CLAIMS_CONFIGURATION`
    for the source of this structure.
    """

    representee_bsn_claim: str
    authorizee_bsn_claim: str
    # could be missing in lax mode, see DIGID_EHERKENNING_OIDC_STRICT feature flag
    mandate_service_id_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]


@register("digid_machtigen_oidc")
class DigiDMachtigenOIDCAuthentication(
    OIDCAuthentication[DigiDmachtigenClaims, OptionsT]
):
    verbose_name = _("DigiD Machtigen via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = "digid_machtigen_oidc:machtigen"
    config_class = OFDigiDMachtigenConfig
    init_view = staticmethod(digid_machtigen_init)
    is_for_gemachtigde = True

    def transform_claims(self, normalized_claims: DigiDmachtigenClaims) -> FormAuth:
        authorizee = normalized_claims["authorizee_bsn_claim"]
        mandate_context = {}
        if "mandate_service_id_claim" in normalized_claims:
            mandate_context["services"] = [
                {"id": normalized_claims["mandate_service_id_claim"]}
            ]
        return {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": normalized_claims["representee_bsn_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
            "legal_subject_identifier_type": "bsn",
            "legal_subject_identifier_value": authorizee,
            "mandate_context": mandate_context,
        }

    def get_label(self) -> str:
        return "DigiD Machtigen"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))


class EHBewindvoeringClaims(TypedDict):
    """
    Processed EH claims structure.

    See :attr:`digid_eherkenning.oidc.models.EHerkenningBewindvoeringConfig.CLAIMS_CONFIGURATION`
    for the source of this structure.
    """

    identifier_type_claim: NotRequired[str]
    legal_subject_claim: str
    acting_subject_claim: str
    branch_number_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]
    representee_claim: str
    # could be missing in lax mode, see DIGID_EHERKENNING_OIDC_STRICT feature flag
    mandate_service_id_claim: NotRequired[str]
    mandate_service_uuid_claim: NotRequired[str]


_EH_IDENTIFIER_TYPE_MAP = {
    "urn:etoegang:1.9:EntityConcernedID:KvKnr": LegalSubjectIdentifierType.kvk,
    "urn:etoegang:1.9:EntityConcernedID:RSIN": LegalSubjectIdentifierType.rsin,
}


@register("eherkenning_bewindvoering_oidc")
class EHerkenningBewindvoeringOIDCAuthentication(
    OIDCAuthentication[EHBewindvoeringClaims, OptionsT]
):
    verbose_name = _("eHerkenning bewindvoering via OpenID Connect")
    # eHerkenning Bewindvoering always is on a personal title via BSN (or so I've been
    # told)
    provides_auth = AuthAttribute.bsn
    session_key = "eherkenning_bewindvoering_oidc:machtigen"
    config_class = OFEHerkenningBewindvoeringConfig
    init_view = staticmethod(eherkenning_bewindvoering_init)
    is_for_gemachtigde = True

    def transform_claims(self, normalized_claims: EHBewindvoeringClaims) -> FormAuth:
        authorizee = normalized_claims["legal_subject_claim"]
        # Assume KVK if claim is not present...
        name_qualifier = normalized_claims.get(
            "identifier_type_claim",
            "urn:etoegang:1.9:EntityConcernedID:KvKnr",
        )
        services = []
        if (
            "mandate_service_id_claim" in normalized_claims
            and "mandate_service_uuid_claim" in normalized_claims
        ):
            services.append(
                {
                    "id": normalized_claims["mandate_service_id_claim"],
                    "uuid": normalized_claims["mandate_service_uuid_claim"],
                }
            )

        form_auth: FormAuth = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": normalized_claims["representee_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
            # representee
            # acting subject
            "acting_subject_identifier_type": "opaque",
            "acting_subject_identifier_value": normalized_claims[
                "acting_subject_claim"
            ],
            # legal subject
            "legal_subject_identifier_type": _EH_IDENTIFIER_TYPE_MAP.get(
                name_qualifier,
                LegalSubjectIdentifierType.kvk,
            ),
            "legal_subject_identifier_value": authorizee,
            # mandate
            "mandate_context": {
                "role": "bewindvoerder",
                "services": services,
            },
        }

        if service_restriction := normalized_claims.get("branch_number_claim", ""):
            form_auth["legal_subject_service_restriction"] = service_restriction
        return form_auth

    def get_label(self) -> str:
        return "eHerkenning bewindvoering"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))
