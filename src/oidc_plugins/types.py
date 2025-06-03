from typing import NotRequired, TypedDict

type ClaimPath = list[str]

class ClaimPathWithLegacy(TypedDict):
    """
    When mozilla_django_oidc_db used solo models, the claims
    were remapped to the names of the fields in the configuration
    The path field is the new claim path, while the legacy field is 
    the name of the old config field.
    """
    path: ClaimPath
    legacy: str

class ClaimProcessingInstructions(TypedDict):
    # Claims that are ALWAYS required, also in lax mode
    always_required_claims: list[ClaimPathWithLegacy]
    # Claims that if missing will raise an error only in strict mode
    strict_required_claims: list[ClaimPathWithLegacy]

class ErrorMessagesMap(TypedDict):
    access_denied: tuple[str, str]

#
# Legacy processed claim structure
# 
class DigiDClaims(TypedDict):
    """
    Processed DigiD claims structure.

    See :attr:`oidc_plugins.plugins.OIDCDigidPlugin.get_claim_processing_instructions` for the
    source of this structure.
    """

    bsn_claim: str
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]

class DigiDmachtigenClaims(TypedDict):
    """
    Processed DigiD Machtigen claims structure.

    See :attr:`oidc_plugins.plugins.OIDCDigiDMachtigenPlugin.get_claim_processing_instructions`
    for the source of this structure.
    """

    representee_bsn_claim: str
    authorizee_bsn_claim: str
    # could be missing in lax mode, see DIGID_EHERKENNING_OIDC_STRICT feature flag
    mandate_service_id_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]

class EHClaims(TypedDict):
    """
    Processed EH claims structure.

    See :attr:`oidc_plugins.plugins.OIDCeHerkenningPlugin.get_claim_processing_instructions`
    for the source of this structure.
    """

    identifier_type_claim: NotRequired[str]
    legal_subject_claim: str
    acting_subject_claim: NotRequired[str]
    branch_number_claim: NotRequired[str]
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]

class EHBewindvoeringClaims(TypedDict):
    """
    Processed EH bewindvoering claims structure.

    See :attr:`oidc_plugins.plugins.OIDCeHerkenningBewindvoeringPlugin.get_claim_processing_instructions`
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