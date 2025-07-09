from __future__ import annotations

from typing import NotRequired, TypedDict, assert_never

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
from ...types import (
    EIDASCompanyContext,
    EIDASContext,
)
from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .constants import EIDAS_COMPANY_PLUGIN_ID, EIDAS_PLUGIN_ID
from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASCompanyConfig,
    OFEIDASConfig,
)
from .views import (
    digid_init,
    digid_machtigen_init,
    eherkenning_bewindvoering_init,
    eherkenning_init,
    eidas_company_init,
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

    legal_subject_identifier_claim: str
    legal_subject_identifier_type_claim: str
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]
    legal_subject_first_name_claim: str
    legal_subject_family_name_claim: str
    legal_subject_date_of_birth_claim: str


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
        match auth_info.attribute:
            case AuthAttribute.national_id:
                legal_subject_identifier_type = "nationalID"
            case AuthAttribute.bsn:
                legal_subject_identifier_type = "bsn"
            case AuthAttribute.pseudo:
                legal_subject_identifier_type = "opaque"
            case _:  # pragma: no cover
                assert_never(auth_info.acting_subject_identifier_type)

        return {
            "source": "eidas",
            "levelOfAssurance": auth_info.loa,
            "authorizee": {
                "legalSubject": {
                    "identifierType": legal_subject_identifier_type,
                    "identifier": auth_info.value,
                    "firstName": auth_info.additional_claims["first_name"],
                    "familyName": auth_info.additional_claims["family_name"],
                    "dateOfBirth": auth_info.additional_claims["date_of_birth"],
                }
            },
        }

    def transform_claims(
        self, options: OptionsT, normalized_claims: EIDASClaims
    ) -> FormAuth:
        legal_subject_identifier_value = normalized_claims[
            "legal_subject_identifier_claim"
        ]

        # If legal_subject_identifier_type isn't provided, or is unknown, fallback to
        # pseudo.
        if (
            legal_subject_identifier_type := normalized_claims.get(
                "legal_subject_identifier_type_claim"
            )
        ) not in AuthAttribute:
            legal_subject_identifier_type = AuthAttribute.pseudo

        return {
            "plugin": self.identifier,
            "loa": str(normalized_claims.get("loa_claim", "")),
            "attribute": legal_subject_identifier_type,
            "value": legal_subject_identifier_value,
            "additional_claims": {
                "first_name": normalized_claims["legal_subject_first_name_claim"],
                "family_name": normalized_claims["legal_subject_family_name_claim"],
                "date_of_birth": normalized_claims["legal_subject_date_of_birth_claim"],
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


class EIDASCompanyClaims(TypedDict):
    """
    Processed eIDAS claims structure.

    See :attr:`digid_eherkenning.oidc.models.EIDASCompanyOIDCAuthentication.CLAIMS_CONFIGURATION`
    for the source of this structure.
    """

    # As the Signicat simulator only returns natural person information, we don't exactly
    # know how this is returned.
    legal_subject_identifier_claim: str
    acting_subject_identifier_claim: str
    acting_subject_identifier_type_claim: str
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]
    legal_subject_name_claim: str
    acting_subject_first_name_claim: str
    acting_subject_family_name_claim: str
    acting_subject_date_of_birth_claim: str

    mandate_service_id_claim: str


@register(EIDAS_COMPANY_PLUGIN_ID)
class EIDASCompanyOIDCAuthentication(OIDCAuthentication[EIDASCompanyClaims, OptionsT]):
    verbose_name = _("eIDAS for companies via OpenID Connect")
    provides_auth = (AuthAttribute.pseudo,)
    session_key = "eidas_company_oidc"
    config_class = OFEIDASCompanyConfig
    init_view = staticmethod(eidas_company_init)
    manage_auth_context = True

    def get_label(self) -> str:
        return "eIDAS for companies"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eidas_logo(request))

    def auth_info_to_auth_context(self, auth_info: AuthInfo) -> EIDASCompanyContext:
        match auth_info.acting_subject_identifier_type:
            case AuthAttribute.national_id:
                acting_subject_identifier_type = "nationalID"
            case AuthAttribute.bsn:
                acting_subject_identifier_type = "bsn"
            case AuthAttribute.pseudo:
                acting_subject_identifier_type = "opaque"
            case _:  # pragma: no cover
                assert_never(auth_info.acting_subject_identifier_type)

        return {
            "source": "eidas",
            "levelOfAssurance": auth_info.loa,
            "authorizee": {
                "legalSubject": {
                    "identifierType": "opaque",
                    "identifier": auth_info.legal_subject_identifier_value,
                    "companyName": auth_info.additional_claims["company_name"],
                },
                "actingSubject": {
                    "identifierType": acting_subject_identifier_type,
                    "identifier": auth_info.acting_subject_identifier_value,
                    "firstName": auth_info.additional_claims["first_name"],
                    "familyName": auth_info.additional_claims["family_name"],
                    "dateOfBirth": auth_info.additional_claims["date_of_birth"],
                },
            },
            "mandate": auth_info.mandate_context,
        }

    def transform_claims(
        self, options: OptionsT, normalized_claims: EIDASCompanyClaims
    ) -> FormAuth:
        acting_subject_identifier_value = normalized_claims[
            "acting_subject_identifier_claim"
        ]

        # If acting_subject_identifier_type isn't provided, or is unknown, fallback to pseudo.
        if (
            acting_subject_identifier_type := normalized_claims.get(
                "acting_subject_identifier_type_claim"
            )
        ) not in AuthAttribute:
            acting_subject_identifier_type = AuthAttribute.pseudo

        loa_value = str(normalized_claims.get("loa_claim", ""))

        mandate_context = {
            "services": [{"id": normalized_claims["mandate_service_id_claim"]}]
        }

        legal_subject_identifier_value = normalized_claims[
            "legal_subject_identifier_claim"
        ]
        return {
            "plugin": self.identifier,
            "loa": loa_value,
            "attribute": AuthAttribute.pseudo,
            "value": legal_subject_identifier_value,
            "legal_subject_identifier_value": legal_subject_identifier_value,
            "legal_subject_identifier_type": "opaque",
            "acting_subject_identifier_value": acting_subject_identifier_value,
            "acting_subject_identifier_type": acting_subject_identifier_type,
            "mandate_context": mandate_context,
            "additional_claims": {
                "first_name": normalized_claims["acting_subject_first_name_claim"],
                "family_name": normalized_claims["acting_subject_family_name_claim"],
                "date_of_birth": normalized_claims[
                    "acting_subject_date_of_birth_claim"
                ],
                "company_name": normalized_claims["legal_subject_name_claim"],
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
