from typing import TypedDict

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
