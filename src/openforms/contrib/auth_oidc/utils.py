from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import structlog
from glom import Path, PathAccessError, assign, glom
from mozilla_django_oidc_db.plugins import OIDCPlugin
from mozilla_django_oidc_db.typing import JSONObject

from openforms.authentication.registry import register as auth_register
from openforms.contrib.auth_oidc.plugin import OIDCAuthentication

from .typing import ClaimPathDetails, ClaimProcessingInstructions

logger = structlog.stdlib.get_logger(__name__)


class NoLOAClaim(Exception):
    pass


class NoAuthPluginFound(Exception):
    pass


def _process_loa(
    claims: JSONObject, claim_processing_instructions: ClaimProcessingInstructions
) -> str:
    default = glom(claim_processing_instructions, "loa_claims.default", default=None)
    if (
        not (
            loa_claim_path := glom(
                claim_processing_instructions, "loa_claims.path_in_claim", default=None
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
        for mapping in glom(
            claim_processing_instructions, "loa_claims.value_mapping", default=[]
        )
    }

    # apply mapping, if not found -> use the literal original value instead
    processed_loa = loa_map.get(loa, loa)
    assert processed_loa
    return processed_loa


def process_claims(
    claims: JSONObject,
    claim_processing_instructions: ClaimProcessingInstructions,
    validate_processed_claims: Callable[[JSONObject]],
    strict: bool = True,
) -> JSONObject:
    """
    Given the raw claims, process them using the provided config.

    Claim processing performs the following steps:

    * Extracting only the needed values. These are configured in the plugin.
      An error is thrown for missing keys that are strictly required
      (also when running in lax mode).
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

    And these are the values of the ``options`` field of an ``OIDCClient`` instance:

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

    Then, if the plugin related to this ``OIDCClient`` instance implements this method:

    .. code:: python

        def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
            config = self.get_config()

            return {
                "always_required_claims": [
                    {
                        "path_in_claim": config.options["bsn_path"],
                        "processed_path": ["bsn_claim"]
                    }
                ],
                "strict_required_claims": [
                    {
                        "path_in_claim": config.options["user_info"]["pet_path"],
                        "processed_path": ["pet"]
                    }
                ],
            }

    The resulting processed claim will be:

    .. code:: json

       {
           "bsn_claim": "123456782",
           "pet": "cat",
           "loa_claim": "urn:etoegang:core:assurance-class:loa1"
       }
    """
    processed_claims = {}

    # Explicitly not adding claims, as these are not obfuscated and
    # contain sensitive info.
    log = logger.bind(
        claim_processing_instructions=claim_processing_instructions, strict=strict
    )

    def _process_claim(
        claim_path: ClaimPathDetails,
        type_claim: Literal[
            "always_required_claims", "strict_required_claims", "optional_claims"
        ],
    ) -> None:
        try:
            value = glom(claims, Path(*claim_path["path_in_claim"]))
        except PathAccessError as exc:
            claim_repr = " > ".join(claim_path["path_in_claim"])

            match type_claim:
                case "always_required_claims":
                    raise ValueError(
                        f"Required claim '{claim_repr}' not found"
                    ) from exc
                case "strict_required_claims":
                    if not strict:
                        return
                    raise ValueError(
                        f"Required claim '{claim_repr}' not found"
                    ) from exc
                case "optional_claims":
                    return

        assign(
            processed_claims, Path(*claim_path["processed_path"]), value, missing=dict
        )

    # Check claims that are required also in lax mode
    for claim_path in claim_processing_instructions["always_required_claims"]:
        _process_claim(claim_path=claim_path, type_claim="always_required_claims")

    # Check the other required claims, here we only raise an error if we are running in strict mode
    for claim_path in claim_processing_instructions["strict_required_claims"]:
        _process_claim(claim_path=claim_path, type_claim="strict_required_claims")

    # Now process any optional claim
    for claim_path in claim_processing_instructions["optional_claims"]:
        _process_claim(claim_path=claim_path, type_claim="optional_claims")

    # Add LoA claims
    try:
        loa = _process_loa(claims, claim_processing_instructions)
    except NoLOAClaim as exc:
        log.info("Missing LoA claim, excluding it from processed claims", exc_info=exc)
    else:
        processed_path = glom(
            claim_processing_instructions, "loa_claims.processed_path", default=None
        )
        assign(processed_claims, Path(*processed_path), loa)

    # Validate the processed claims
    validate_processed_claims(processed_claims)

    return processed_claims


def get_of_auth_plugin(oidc_plugin: OIDCPlugin) -> OIDCAuthentication:
    """Get the Open Forms authentication plugin corresponding to the provided OIDC plugin."""
    for plugin in auth_register:
        if not isinstance(plugin, OIDCAuthentication):
            continue
        if plugin.oidc_plugin_identifier == oidc_plugin.identifier:
            return plugin
    else:
        raise NoAuthPluginFound()
