from typing import NotRequired, TypedDict

from mozilla_django_oidc_db.typing import ClaimPath


class ClaimPathDetails(TypedDict):
    """
    When mozilla_django_oidc_db used solo models, the claims
    were remapped to the names of the fields in the configuration
    The path field is the new claim path, while the legacy field is
    the name of the old config field.
    """

    path_in_claim: ClaimPath
    processed_path: ClaimPath


# Defining this way, because "from" is a reserved python keyword
LoaValueMapping = TypedDict("LoaValueMapping", {"from": str | int, "to": str})


class LoaClaimInstructions(TypedDict):
    default: str
    value_mapping: list[LoaValueMapping]
    path_in_claim: ClaimPath
    processed_path: ClaimPath


class ClaimProcessingInstructions(TypedDict):
    # Claims that are ALWAYS required, also in lax mode
    always_required_claims: list[ClaimPathDetails]
    # Claims that if missing will raise an error only in strict mode
    strict_required_claims: list[ClaimPathDetails]
    optional_claims: list[ClaimPathDetails]
    loa_claims: LoaClaimInstructions


#
# Legacy processed claim structure
#
class DigiDClaims(TypedDict):
    """
    Processed DigiD claims structure.

    See :attr:`openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.plugins.OIDCDigidPlugin.get_claim_processing_instructions` for the
    source of this structure.
    """

    bsn_claim: str
    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]


class DigiDmachtigenClaims(TypedDict):
    """
    Processed DigiD Machtigen claims structure.

    See :attr:`openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.plugins.OIDCDigiDMachtigenPlugin.get_claim_processing_instructions`
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

    See :attr:`openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.plugins.OIDCeHerkenningPlugin.get_claim_processing_instructions`
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

    See :attr:`openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.plugins.OIDCeHerkenningBewindvoeringPlugin.get_claim_processing_instructions`
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


class OIDCErrors(TypedDict):
    access_denied: NotRequired[tuple[str, str]]
