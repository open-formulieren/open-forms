import structlog
from glom import Path, PathAccessError, assign, glom
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.typing import JSONObject

from .types import ClaimPathWithLegacy, ClaimProcessingInstructions

logger = structlog.stdlib.get_logger(__name__)


class NoLOAClaim(Exception):
    pass


def process_claims(
    claims: JSONObject,
    config: OIDCClient,
    claim_processing_instructions: ClaimProcessingInstructions,
    strict: bool = True,
    legacy: bool = False,
) -> JSONObject:
    """
    Given the raw claims, process them using the provided config.

    Claim processing performs the following steps:
    * Extracting only the needed values. These are configured in the plugin. An error is thrown for missing keys that are strictly required (also when running in lax mode).
    * Extracting and re-mapping the LoA values (if needed).

    For example, if this is the claim received from the IdP:

    .. code:: json

       {
           "bsn": "123456782",
           "user": {
               "pet": "cat",
               "some": "other info"
           },
           "loa": "urn:etoegang:core:assurance-class:loa1"
       }

    And these are the values of the configuration options, in an instance of ``OIDCClient``:

    .. code:: json

       {
           "bsn_path": ["bsn"],
           "user_info": {
               "pet_path": ["user", "pet"],
           },
           "other_config": "bla",
           "loa_settings": {
               "claim_path": ["loa"]
           }
       }

    Then, if the plugin related to this OIDCClient instance implements this method:

    .. code:: python

        def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
            config = self.get_config()

            return {
                "always_required_claims": [
                    {
                        "path": config.options["bsn_path"],
                        "legacy": "bsn_claim"
                    }
                ],
                "strict_required_claims": [
                    {
                        "path": config.options["user_info"]["pet_path"],
                        "legacy": "pet"
                    }
                ],
            }

    The resulting processed claim will be (in non-legacy mode):

    .. code:: json

       {
           "bsn": "123456782",
           "user": {
               "pet": "cat",
           },
           "loa": "urn:etoegang:core:assurance-class:loa1"
       }

    While in legacy mode, this will give:

    .. code:: json

       {
           "bsn_claim": "123456782",
           "pet": "cat",
           "loa_claim": "urn:etoegang:core:assurance-class:loa1"
       }
    """
    processed_claims = {}

    def add_to_claims(
        processed_claims: dict, claim_path: ClaimPathWithLegacy, value: JSONObject
    ) -> None:
        path_in_processed_claim = (
            Path(claim_path["legacy"]) if legacy else Path(*claim_path["path"])
        )
        assign(processed_claims, path_in_processed_claim, value)

    # Check claims that are required also in lax mode
    for claim_path in claim_processing_instructions["always_required_claims"]:
        try:
            value = glom(claims, Path(*claim_path["path"]))
        except PathAccessError as exc:
            claim_repr = " > ".join(claim_path["path"])
            raise ValueError(f"Required claim '{claim_repr}' not found") from exc

        add_to_claims(processed_claims, claim_path, value)

    # Check the other required claims, here we only raise an error if we are running in strict mode
    for claim_path in claim_processing_instructions["strict_required_claims"]:
        try:
            value = glom(claims, Path(*claim_path["path"]))
        except PathAccessError as exc:
            if not strict:
                continue
            claim_repr = " > ".join(claim_path["path"])
            raise ValueError(f"Required claim '{claim_repr}' not found") from exc

        add_to_claims(processed_claims, claim_path, value)

    # Now process any optional claim
    for claim_path in claim_processing_instructions["optional_claims"]:
        try:
            value = glom(claims, Path(*claim_path["path"]))
        except PathAccessError:
            continue

        add_to_claims(processed_claims, claim_path, value)

    # Add LoA claims
    loa_claim_path = config.options["loa_settings"]["claim_path"]
    try:
        loa = _process_loa(claims, config)
    except NoLOAClaim as exc:
        logger.info(
            "Missing LoA claim, excluding it from processed claims", exc_info=exc
        )
    else:
        path_in_processed_claim = Path("loa_claim") if legacy else Path(*loa_claim_path)
        assign(processed_claims, path_in_processed_claim, loa)

    return processed_claims


def _process_loa(claims: JSONObject, config: OIDCClient) -> str:
    default = glom(config.options, "loa_settings.default", default=None)
    if (
        not (
            loa_claim_path := glom(
                config.options, "loa_settings.claim_path", default=None
            )
        )
        and not default
    ):
        raise NoLOAClaim("No LoA claim or default LoA configured")

    if not loa_claim_path:
        return default

    try:
        loa = glom(claims, Path(*loa_claim_path))
        loa_claim_missing = False
    except PathAccessError:
        # default could be empty (string)!
        loa = default
        loa_claim_missing = not default

    if loa_claim_missing:
        raise NoLOAClaim("LoA claim is absent and no default LoA configured")

    # 'from' is string or number, which are valid keys
    loa_map: dict[str | float | int, str] = {
        mapping["from"]: mapping["to"]
        for mapping in glom(config.options, "loa_settings.value_mapping", default=[])
    }

    # apply mapping, if not found -> use the literal original value instead
    processed_loa = loa_map.get(loa, loa)
    assert processed_loa
    return processed_loa
