from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.schemas import LOA_MAPPING_SCHEMA

from .constants import EIDASAssuranceLevels

EIDAS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Options",
    "description": _("OIDC eIDAS Configuration options."),
    "type": "object",
    "required": ["identity_settings"],
    "properties": {
        "loa_settings": {
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "claim_path": {
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
                "default": {
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in EIDASAssuranceLevels.choices
                    ],
                },
                "value_mapping": LOA_MAPPING_SCHEMA,
            },
        },
        "identity_settings": {
            "description": _("eIDAS identity settings."),
            "type": "object",
            "required": [
                "legal_subject_identifier_claim_path",
                "legal_subject_identifier_type_claim_path",
                "legal_subject_first_name_claim_path",
                "legal_subject_family_name_claim_path",
                "legal_subject_date_of_birth_claim_path",
            ],
            "properties": {
                "legal_subject_identifier_claim_path": {
                    "description": _(
                        "Path to the claim value holding the identifier of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:PseudoID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_identifier_type_claim_path": {
                    "description": _(
                        "Path to the claim value that specifies how the person identifier claim must be interpreted. "
                        "The expected claim value is one of: 'bsn', 'pseudo' or 'national_id'."
                    ),
                    "default": ["namequalifier"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_first_name_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal first name of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FirstName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_family_name_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal family name of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FamilyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_date_of_birth_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal birthdate of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:DateOfBirth"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
    },
}

EIDAS_COMPANY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Options",
    "description": _("OIDC eIDAS company configuration options."),
    "type": "object",
    "required": ["identity_settings"],
    "properties": {
        "loa_settings": {
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "claim_path": {
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
                "default": {
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in EIDASAssuranceLevels.choices
                    ],
                },
                "value_mapping": LOA_MAPPING_SCHEMA,
            },
        },
        "identity_settings": {
            "description": _("eIDAS identity settings."),
            "type": "object",
            "required": [
                "legal_subject_identifier_claim_path",
                "legal_subject_name_claim_path",
                "acting_subject_identifier_claim_path",
                "acting_subject_identifier_type_claim_path",
                "acting_subject_first_name_claim_path",
                "acting_subject_family_name_claim_path",
                "legal_subject_date_of_birth_claim_path",
                "mandate_service_id_claim_path",
            ],
            "properties": {
                "legal_subject_identifier_claim_path": {
                    "description": _(
                        "Path to the claim value holding the identifier of the authenticated company."
                    ),
                    "default": [
                        "urn:etoegang:1.11:EntityConcernedID:eIDASLegalIdentifier"
                    ],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_name_claim_path": {
                    "description": _(
                        "Path to the claim that holds the name of the authenticated company."
                    ),
                    "default": ["urn:etoegang:1.11:attribute-represented:CompanyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_identifier_claim_path": {
                    "description": _(
                        "Path to the claim value that holds identifier of the acting subject."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:PseudoID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_identifier_type_claim_path": {
                    "description": _(
                        "Path to the claim value that specifies how the acting subject identifier claim must be "
                        "interpreted. The expected claim value is one of: 'bsn', 'pseudo' or "
                        "'national_id'."
                    ),
                    "default": ["namequalifier"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_first_name_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal first name of the acting subject."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FirstName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_family_name_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal family name of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FamilyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_date_of_birth_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the legal birthdate of the acting subject."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:DateOfBirth"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "mandate_service_id_claim_path": {
                    "description": _(
                        "Path to the claim value that holds the service ID for which the acting subject "
                        "is authorized."
                    ),
                    "default": ["urn:etoegang:core:ServiceID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
    },
}
