from __future__ import annotations

from typing import TypedDict, assert_never, final

from django.utils.translation import gettext_lazy as _

from flags.state import flag_enabled

from openforms.authentication.base import LoginLogo
from openforms.authentication.contrib.digid.views import (
    DIGID_MESSAGE_PARAMETER,
    LOGIN_CANCELLED as DIGID_LOGIN_CANCELLED,
)
from openforms.authentication.contrib.eherkenning.views import (
    LOGIN_CANCELLED as EH_LOGIN_CANCELLED,
    MESSAGE_PARAMETER as EH_MESSAGE_PARAMETER,
)
from openforms.authentication.models import AuthInfo
from openforms.authentication.registry import register
from openforms.authentication.types import EIDASCompanyContext, EIDASContext
from openforms.authentication.typing import FormAuth
from openforms.contrib.auth_oidc.plugin import OIDCAuthentication
from openforms.contrib.auth_oidc.typing import (
    DigiDClaims,
    DigiDmachtigenClaims,
    EHBewindvoeringClaims,
    EHClaims,
    EIDASClaims,
    EIDASCompanyClaims,
    OIDCErrors,
)
from openforms.contrib.digid_eherkenning.utils import (
    get_digid_logo,
    get_eherkenning_logo,
    get_eidas_logo,
)

from ...constants import (
    AuthAttribute,
    LegalSubjectIdentifierType,
)
from .constants import EIDAS_COMPANY_PLUGIN_ID, EIDAS_PLUGIN_ID
from .oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
    EIDASAssuranceLevels,
)

OIDC_ID_TOKEN_SESSION_KEY = "oidc_id_token"


@final
class NoOptions(TypedDict):
    pass


@register("digid_oidc")
class DigiDOIDCAuthentication(OIDCAuthentication[DigiDClaims, NoOptions]):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = (AuthAttribute.bsn,)
    oidc_plugin_identifier = OIDC_DIGID_IDENTIFIER

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))

    def transform_claims(
        self, options: NoOptions, normalized_claims: DigiDClaims
    ) -> FormAuth:
        return {
            "plugin": self.identifier,
            "attribute": self.provides_auth[0],
            "value": normalized_claims["bsn_claim"],
            "loa": str(normalized_claims.get("loa_claim", "")),
        }

    def get_error_codes(self) -> OIDCErrors:
        return {"access_denied": (DIGID_MESSAGE_PARAMETER, DIGID_LOGIN_CANCELLED)}


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(OIDCAuthentication[EHClaims, NoOptions]):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = (AuthAttribute.kvk,)
    oidc_plugin_identifier = OIDC_EH_IDENTIFIER

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))

    def transform_claims(
        self, options: NoOptions, normalized_claims: EHClaims
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

    def get_error_codes(self) -> OIDCErrors:
        eh_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier.split("_")[0]
        }
        return {"access_denied": (eh_message_parameter, EH_LOGIN_CANCELLED)}


@register(EIDAS_PLUGIN_ID)
class EIDASOIDCAuthentication(OIDCAuthentication[EIDASClaims, NoOptions]):
    verbose_name = _("eIDAS via OpenID Connect")
    provides_auth = (AuthAttribute.bsn, AuthAttribute.pseudo,)
    oidc_plugin_identifier = OIDC_EIDAS_IDENTIFIER
    manage_auth_context = True
    provides_multiple_auth_attributes = True

    def get_label(self) -> str:
        return "eIDAS"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eidas_logo(request))

    def auth_info_to_auth_context(self, auth_info: AuthInfo) -> EIDASContext:
        match auth_info.attribute:
            case AuthAttribute.bsn:
                legal_subject_identifier_type = "bsn"
            case AuthAttribute.pseudo:
                legal_subject_identifier_type = "opaque"
            case _:  # pragma: no cover
                assert_never(auth_info.acting_subject_identifier_type)

        return {
            "source": "eidas",
            "levelOfAssurance": EIDASAssuranceLevels(auth_info.loa).value,
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
        self, options: NoOptions, normalized_claims: EIDASClaims
    ) -> FormAuth:
        legal_subject_bsn_identifier_value = normalized_claims.get(
            "legal_subject_bsn_identifier_claim"
        )
        legal_subject_pseudo_identifier_value = normalized_claims.get(
            "legal_subject_pseudo_identifier_claim"
        )

        legal_subject_identifier_type = (
            AuthAttribute.bsn
            if legal_subject_bsn_identifier_value is not None
            else AuthAttribute.pseudo
        )

        return {
            "plugin": self.identifier,
            "loa": str(normalized_claims.get("loa_claim", "")),
            "attribute": legal_subject_identifier_type,
            "value": legal_subject_bsn_identifier_value
            or legal_subject_pseudo_identifier_value,
            "additional_claims": {
                "first_name": normalized_claims["legal_subject_first_name_claim"],
                "family_name": normalized_claims["legal_subject_family_name_claim"],
                "date_of_birth": normalized_claims["legal_subject_date_of_birth_claim"],
            },
        }

    def get_error_codes(self) -> OIDCErrors:
        eIDAS_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier.split("_")[0]
        }
        return {"access_denied": (eIDAS_message_parameter, EH_LOGIN_CANCELLED)}


@register(EIDAS_COMPANY_PLUGIN_ID)
class EIDASCompanyOIDCAuthentication(OIDCAuthentication[EIDASCompanyClaims, NoOptions]):
    verbose_name = _("eIDAS for companies via OpenID Connect")
    provides_auth = (AuthAttribute.pseudo,)
    manage_auth_context = True
    oidc_plugin_identifier = OIDC_EIDAS_COMPANY_IDENTIFIER

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
            "levelOfAssurance": EIDASAssuranceLevels(auth_info.loa).value,
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
        self, options: NoOptions, normalized_claims: EIDASCompanyClaims
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

    def get_error_codes(self) -> OIDCErrors:
        eIDAS_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier.split("_")[0]
        }
        return {"access_denied": (eIDAS_message_parameter, EH_LOGIN_CANCELLED)}


@register("digid_machtigen_oidc")
class DigiDMachtigenOIDCAuthentication(
    OIDCAuthentication[DigiDmachtigenClaims, NoOptions]
):
    verbose_name = _("DigiD Machtigen via OpenID Connect")
    provides_auth = (AuthAttribute.bsn,)
    oidc_plugin_identifier = OIDC_DIGID_MACHTIGEN_IDENTIFIER
    is_for_gemachtigde = True

    def transform_claims(
        self, options: NoOptions, normalized_claims: DigiDmachtigenClaims
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

    def get_label(self) -> str:
        return "DigiD Machtigen"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))

    def get_error_codes(self) -> OIDCErrors:
        return {"access_denied": (DIGID_MESSAGE_PARAMETER, DIGID_LOGIN_CANCELLED)}


_EH_IDENTIFIER_TYPE_MAP = {
    "urn:etoegang:1.9:EntityConcernedID:KvKnr": LegalSubjectIdentifierType.kvk,
    "urn:etoegang:1.9:EntityConcernedID:RSIN": LegalSubjectIdentifierType.rsin,
}


@register("eherkenning_bewindvoering_oidc")
class EHerkenningBewindvoeringOIDCAuthentication(
    OIDCAuthentication[EHBewindvoeringClaims, NoOptions]
):
    verbose_name = _("eHerkenning bewindvoering via OpenID Connect")
    # eHerkenning Bewindvoering always is on a personal title via BSN (or so I've been
    # told)
    provides_auth = (AuthAttribute.bsn,)
    oidc_plugin_identifier = OIDC_EH_BEWINDVOERING_IDENTIFIER
    is_for_gemachtigde = True

    def transform_claims(
        self, options: NoOptions, normalized_claims: EHBewindvoeringClaims
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

    def get_label(self) -> str:
        return "eHerkenning bewindvoering"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))

    def get_error_codes(self) -> OIDCErrors:
        eh_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier.split("_")[0]
        }
        return {"access_denied": (eh_message_parameter, EH_LOGIN_CANCELLED)}
