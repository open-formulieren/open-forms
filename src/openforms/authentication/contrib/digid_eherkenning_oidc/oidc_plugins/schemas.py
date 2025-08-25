from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.schemas import get_loa_mapping_schema

from .constants import EIDASAssuranceLevels

EIDAS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Options",
    "description": _("OIDC eIDAS Configuration options."),
    "type": "object",
    "required": ["identity_settings"],
    "properties": {
        "loa_settings": {
            "title": _("LoA settings"),
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "claim_path": {
                    "title": _("Claim path"),
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
                    "title": _("Default"),
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in EIDASAssuranceLevels.choices
                    ],
                },
                "value_mapping": get_loa_mapping_schema(EIDASAssuranceLevels),
            },
        },
        "identity_settings": {
            "title": _("Identity settings"),
            "description": _("eIDAS identity settings."),
            "type": "object",
            "required": [
                "legal_subject_bsn_identifier_claim_path",
                "legal_subject_pseudo_identifier_claim_path",
                "legal_subject_first_name_claim_path",
                "legal_subject_family_name_claim_path",
                "legal_subject_date_of_birth_claim_path",
            ],
            "properties": {
                "legal_subject_bsn_identifier_claim_path": {
                    "title": ("Legal subject bsn identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the bsn identifier of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:BSN"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_pseudo_identifier_claim_path": {
                    "title": _("Legal subject pseudo identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the pseudo identifier of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:PseudoID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_first_name_claim_path": {
                    "title": _("Legal subject first name claim path"),
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
                    "title": _("Legal subject family name claim path"),
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
                    "title": _("Legal subject date of birth claim path"),
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
            "title": _("LoA settings"),
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "claim_path": {
                    "title": _("Claim path"),
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
                    "title": _("Default"),
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in EIDASAssuranceLevels.choices
                    ],
                },
                "value_mapping": get_loa_mapping_schema(EIDASAssuranceLevels),
            },
        },
        "identity_settings": {
            "title": _("Identity settings"),
            "description": _("eIDAS identity settings."),
            "type": "object",
            "required": [
                "legal_subject_identifier_claim_path",
                "legal_subject_name_claim_path",
                "acting_subject_bsn_identifier_claim_path",
                "acting_subject_pseudo_identifier_claim_path",
                "acting_subject_first_name_claim_path",
                "acting_subject_family_name_claim_path",
                "acting_subject_date_of_birth_claim_path",
                "mandate_service_id_claim_path",
            ],
            "properties": {
                "legal_subject_identifier_claim_path": {
                    "title": _("Legal subject identifier claim path"),
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
                    "title": _("Legal subject name claim path"),
                    "description": _(
                        "Path to the claim that holds the name of the authenticated company."
                    ),
                    "default": ["urn:etoegang:1.11:attribute-represented:CompanyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_bsn_identifier_claim_path": {
                    "title": _("Acting subject bsn identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the bsn identifier of the acting subject."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:BSN"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_pseudo_identifier_claim_path": {
                    "title": _("Acting subject pseudo identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the pseudo identifier of the acting subject."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:PseudoID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "acting_subject_first_name_claim_path": {
                    "title": _("Acting subject first name claim path"),
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
                    "title": _("Acting subject family name claim path"),
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
                    "title": _("Acting subject date of birth claim path"),
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
                    "title": _("Mandate service id claim path"),
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
