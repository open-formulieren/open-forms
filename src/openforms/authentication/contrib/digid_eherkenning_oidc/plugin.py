from __future__ import annotations

from typing import NotRequired, TypedDict

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from flags.state import flag_enabled

from openforms.authentication.constants import LegalSubjectIdentifierType
from openforms.authentication.contrib.digid.views import (
    DIGID_MESSAGE_PARAMETER,
    LOGIN_CANCELLED,
)
from openforms.authentication.contrib.eherkenning.views import (
    MESSAGE_PARAMETER as EH_MESSAGE_PARAMETER,
)
from openforms.authentication.typing import FormAuth
from openforms.contrib.auth_oidc.plugin import OIDCAuthentication
from openforms.contrib.digid_eherkenning.utils import (
    get_digid_logo,
    get_eherkenning_logo,
    get_eidas_logo,
)

from ...base import LoginLogo
from ...constants import AuthAttribute
from ...models import AuthInfo
from ...registry import register
from ...types import EIDASContext
from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .constants import EIDAS_PLUGIN_ID
from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASConfig,
)
from .views import (
    digid_init,
    digid_machtigen_init,
    eherkenning_bewindvoering_init,
    eherkenning_init,
    eidas_init,
)


class OptionsT(TypedDict):
    pass


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
    provides_auth = (AuthAttribute.bsn,)
    session_key = "digid_oidc:bsn"
    config_class = OFDigiDConfig
    init_view = staticmethod(digid_init)

    def strict_mode(self, request: HttpRequest) -> bool:
        return flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request)

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                return (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def transform_claims(
        self, options: OptionsT, normalized_claims: DigiDClaims
    ) -> FormAuth:
        return {
            "plugin": self.identifier,
            "attribute": self.provides_auth[0],
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
    provides_auth = (AuthAttribute.kvk,)
    session_key = "eherkenning_oidc:kvk"
    config_class = OFEHerkenningConfig
    init_view = staticmethod(eherkenning_init)

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))

    def strict_mode(self, request: HttpRequest) -> bool:
        return flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request)

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                eh_message_parameter = EH_MESSAGE_PARAMETER % {
                    "plugin_id": self.identifier.split("_")[0]
                }
                return (eh_message_parameter, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def transform_claims(
        self, options: OptionsT, normalized_claims: EHClaims
    ) -> FormAuth:
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
            "attribute": self.provides_auth[0],
            "value": normalized_claims["legal_subject_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
            "acting_subject_identifier_type": "opaque",
            "acting_subject_identifier_value": acting_subject_identifier_value
            or "dummy-set-by@openforms",
        }
        if service_restriction := normalized_claims.get("branch_number_claim", ""):
            form_auth["legal_subject_service_restriction"] = service_restriction
        return form_auth


class EIDASClaims(TypedDict):
    """
    Processed eIDAS claims structure.

    See :attr:`digid_eherkenning.oidc.models.OFEIDASConfig.CLAIMS_CONFIGURATION`
    for the source of this structure.
    """

    person_identifier_claim: str
    person_identifier_type_claim: NotRequired[str]
    mandate_service_id_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]
    first_name_claim: str
    family_name_claim: str
    date_of_birth_claim: str

    # As the Signicat simulator only returns natural person information, we don't exactly
    # know how this is returned.
    company_name_claim: NotRequired[str]
    company_legal_identifier_claim: NotRequired[str]
    company_identifier_claim: NotRequired[str]
    company_identifier_type_claim: NotRequired[str]


@register(EIDAS_PLUGIN_ID)
class EIDASOIDCAuthentication(OIDCAuthentication[EIDASClaims, OptionsT]):
    verbose_name = _("eIDAS via OpenID Connect")
    provides_auth = (
        AuthAttribute.bsn,
        AuthAttribute.national_id,
        AuthAttribute.pseudo,
    )
    session_key = "eidas_oidc"
    config_class = OFEIDASConfig
    init_view = staticmethod(eidas_init)
    manage_auth_context = True
    provides_multiple_auth_attributes = True

    def get_label(self) -> str:
        return "eIDAS"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eidas_logo(request))

    def auth_info_to_auth_context(self, auth_info: AuthInfo) -> EIDASContext:
        is_person_legal_subject = self.acting_subject_identifier_value == ""

        person_info = {
            "firstName": self.additional_claims["first_name"],
            "familyName": self.additional_claims["family_name"],
            "dateOfBirth": self.additional_claims["date_of_birth"],
        }

        if is_person_legal_subject:
            # Authentication as natural person
            legal_subject = {
                "identifierType": self.legal_subject_identifier_type,
                "identifier": self.legal_subject_identifier_value,
                **person_info,
            }
            authorizee = {"legalSubject": legal_subject}
        else:
            # Authentication as company
            legal_subject = {
                "identifierType": self.legal_subject_identifier_type,
                "identifier": self.legal_subject_identifier_value,
                "companyName": self.additional_claims["company_name"],
            }
            acting_subject = {
                "identifierType": self.acting_subject_identifier_type,
                "identifier": self.acting_subject_identifier_value,
                **person_info,
            }
            authorizee = {
                "legalSubject": legal_subject,
                "actingSubject": acting_subject,
            }

        return {
            "source": "eidas",
            "levelOfAssurance": self.loa,
            "authorizee": authorizee,
        }

    def transform_claims(
        self, options: OptionsT, normalized_claims: EIDASClaims
    ) -> FormAuth:
        person_identifier_value = normalized_claims["person_identifier_claim"]

        # If person_identifier_type isn't provided, or is unknown, fallback to pseudo.
        if (
            person_identifier_type := normalized_claims.get(
                "person_identifier_type_claim"
            )
        ) not in AuthAttribute:
            person_identifier_type = AuthAttribute.pseudo

        is_person_legal_subject = (
            normalized_claims.get("company_identifier_claim", None) is None
        )

        loa_value = str(normalized_claims.get("loa_claim", ""))

        mandate_context = {}
        if "mandate_service_id_claim" in normalized_claims:
            mandate_context["services"] = [
                {"id": normalized_claims["mandate_service_id_claim"]}
            ]

        # Authentication for natural person
        if is_person_legal_subject:
            return {
                "plugin": self.identifier,
                "loa": loa_value,
                "attribute": person_identifier_type,
                "value": person_identifier_value,
                "legal_subject_identifier_value": person_identifier_value,
                "legal_subject_identifier_type": person_identifier_type,
                "mandate_context": mandate_context,
                "additional_claims": {
                    "first_name": normalized_claims["first_name_claim"],
                    "family_name": normalized_claims["family_name_claim"],
                    "date_of_birth": normalized_claims["date_of_birth_claim"],
                },
            }

        company_identifier_value = normalized_claims["company_identifier_claim"]
        return {
            "plugin": self.identifier,
            "loa": loa_value,
            "attribute": AuthAttribute.pseudo,
            "value": company_identifier_value,
            "legal_subject_identifier_value": company_identifier_value,
            "legal_subject_identifier_type": "opaque",
            "acting_subject_identifier_value": person_identifier_value,
            "acting_subject_identifier_type": person_identifier_type,
            "mandate_context": mandate_context,
            "additional_claims": {
                "first_name": normalized_claims["first_name_claim"],
                "family_name": normalized_claims["family_name_claim"],
                "date_of_birth": normalized_claims["date_of_birth_claim"],
                "company_name": normalized_claims["company_name_claim"],
            },
        }

    def strict_mode(self, request: HttpRequest) -> bool:
        return flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request)

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                eIDAS_message_parameter = EH_MESSAGE_PARAMETER % {
                    "plugin_id": self.identifier.split("_")[0]
                }
                return (eIDAS_message_parameter, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)


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
    provides_auth = (AuthAttribute.bsn,)
    session_key = "digid_machtigen_oidc:machtigen"
    config_class = OFDigiDMachtigenConfig
    init_view = staticmethod(digid_machtigen_init)
    is_for_gemachtigde = True

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                return (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def transform_claims(
        self, options: OptionsT, normalized_claims: DigiDmachtigenClaims
    ) -> FormAuth:
        authorizee = normalized_claims["authorizee_bsn_claim"]
        mandate_context = {}
        if "mandate_service_id_claim" in normalized_claims:
            mandate_context["services"] = [
                {"id": normalized_claims["mandate_service_id_claim"]}
            ]
        return {
            "plugin": self.identifier,
            "attribute": self.provides_auth[0],
            "value": normalized_claims["representee_bsn_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
            "legal_subject_identifier_type": "bsn",
            "legal_subject_identifier_value": authorizee,
            "mandate_context": mandate_context,
        }

    def strict_mode(self, request: HttpRequest) -> bool:
        return flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request)

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
    provides_auth = (AuthAttribute.bsn,)
    session_key = "eherkenning_bewindvoering_oidc:machtigen"
    config_class = OFEHerkenningBewindvoeringConfig
    init_view = staticmethod(eherkenning_bewindvoering_init)
    is_for_gemachtigde = True

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        match error, error_description:
            case ("access_denied", "The user cancelled"):
                eh_message_parameter = EH_MESSAGE_PARAMETER % {
                    "plugin_id": self.identifier.split("_")[0]
                }
                return (eh_message_parameter, LOGIN_CANCELLED)

            case _:
                return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def transform_claims(
        self, options: OptionsT, normalized_claims: EHBewindvoeringClaims
    ) -> FormAuth:
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
            "attribute": self.provides_auth[0],
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

    def strict_mode(self, request: HttpRequest) -> bool:
        return flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request)

    def get_label(self) -> str:
        return "eHerkenning bewindvoering"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))
