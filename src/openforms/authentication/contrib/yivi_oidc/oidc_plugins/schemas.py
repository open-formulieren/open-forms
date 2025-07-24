from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from digid_eherkenning.oidc.schemas import LOA_MAPPING_SCHEMA

YIVI_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Options",
    "description": _("OIDC Yivi configuration options."),
    "type": "object",
    "required": [],
    "properties": {
        "loa_settings": {
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "bsn_loa_claim_path": {
                    "description": _(
                        "Path to the claim value holding the level of assurance. If left empty, it is "
                        "assumed there is no LOA claim and the configured fallback value will be "
                        "used."
                    ),
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "bsn_default_loa": {
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in DigiDAssuranceLevels.choices
                    ],
                },
                "bsn_loa_value_mapping": {
                    **LOA_MAPPING_SCHEMA,
                    "description": _(
                        "Level of assurance claim value mappings. Useful if the values in the LOA "
                        "claim are proprietary, so you can translate them into their standardized "
                        "identifiers."
                    ),
                },
                "kvk_loa_claim_path": {
                    "description": _(
                        "Path to the claim value holding the level of assurance. If left empty, it is "
                        "assumed there is no LOA claim and the configured fallback value will be "
                        "used."
                    ),
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "kvk_default_loa": {
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in AssuranceLevels.choices
                    ],
                },
                "kvk_loa_value_mapping": {
                    **LOA_MAPPING_SCHEMA,
                    "description": _(
                        "Level of assurance claim value mappings. Useful if the values in the LOA "
                        "claim are proprietary, so you can translate them into their standardized "
                        "identifiers."
                    ),
                },
            },
        },
        "identity_settings": {
            "description": _("Yivi identity settings."),
            "type": "object",
            "properties": {
                "bsn_claim_path": {
                    "description": _(
                        "Path to the claim value holding the authenticated user's BSN."
                    ),
                    "default": ["bsn"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "kvk_claim_path": {
                    "description": _(
                        "Path to the claim value holding the KVK identifier of the authenticated company."
                    ),
                    "default": ["kvk"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "pseudo_claim_path": {
                    "description": _(
                        "Path to the claim  value holding the (opaque) identifier of the user. "
                        "This claim will be used when the pseudo authentication option is used, or "
                        "when the plugin is set to anonymous authentication "
                        "(when no authentication options are selected)."
                    ),
                    "default": ["pbdf.sidn-pbdf.irma.pseudonym"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
    },
}
