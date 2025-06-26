import copy
from pathlib import Path

from django.test import override_settings

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from django_webtest import WebTest
from glom import assign
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient, OIDCProvider

from oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_ORG_IDENTIFIER,
)
from openforms.typing import JSONObject
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "data").resolve()


# def mock_config(model: str, **overrides):
#     overrides.setdefault("oidc_op_logout_endpoint", f"{KEYCLOAK_BASE_URL}/logout")
#     return mock_oidc_db_config(
#         app_label="digid_eherkenning_oidc", model=model, **overrides
#     )


# mock_digid_config = partial(
#     mock_config,
#     model="OFDigiDConfig",
#     oidc_rp_scopes_list=["openid", "bsn"],
#     loa_claim=["authsp_level"],
#     default_loa=DigiDAssuranceLevels.middle,
# )

# mock_eherkenning_config = partial(
#     mock_config,
#     model="OFEHerkenningConfig",
#     oidc_rp_scopes_list=["openid", "kvk"],
#     identifier_type_claim=["name_qualifier"],
#     legal_subject_claim=["legalSubjectID"],
#     acting_subject_claim=["actingSubjectID"],
#     branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
#     loa_claim=["authsp_level"],
#     default_loa=AssuranceLevels.low_plus,
# )

# mock_digid_machtigen_config = partial(
#     mock_config,
#     model="OFDigiDMachtigenConfig",
#     oidc_rp_scopes_list=["openid", "bsn"],
#     representee_bsn_claim=["aanvrager.bsn"],
#     authorizee_bsn_claim=["gemachtigde.bsn"],
#     mandate_service_id_claim=["service_id"],
#     loa_claim=["authsp_level"],
#     default_loa=DigiDAssuranceLevels.middle,
# )

# mock_eherkenning_bewindvoering_config = partial(
#     mock_config,
#     model="OFEHerkenningBewindvoeringConfig",
#     oidc_rp_scopes_list=["openid", "bsn"],
#     identifier_type_claim=["name_qualifier"],
#     legal_subject_claim=["legalSubjectID"],
#     acting_subject_claim=["actingSubjectID"],
#     branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
#     representee_claim=["representeeBSN"],
#     mandate_service_id_claim=["service_id"],
#     mandate_service_uuid_claim=["service_uuid"],
#     loa_claim=["authsp_level"],
#     default_loa=AssuranceLevels.low_plus,
# )


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class IntegrationTestsBase(OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES


CLIENT_DEFAULT_OPTIONS = {
    OIDC_ADMIN_CONFIG_IDENTIFIER: {
        "user_settings": {
            "claim_mappings": {
                "username": ["sub"],
                "first_name": [],
                "last_name": [],
                "email": [],
            },
            "username_case_sensitive": True,
            "sensitive_claims": [],
        },
        "groups_settings": {
            "claim_mapping": ["groups"],
            "sync": True,
            "sync_pattern": "*",
            "make_users_staff": False,
            "superuser_group_names": [],
            "default_groups": [],
        },
    },
    OIDC_DIGID_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": DigiDAssuranceLevels.middle,
            "value_mapping": [],
        },
        "identity_settings": {
            "bsn_claim_path": ["bsn"],
        },
    },
    OIDC_EH_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": AssuranceLevels.low_plus,
            "value_mapping": [],
        },
        "identity_settings": {
            "identifier_type_claim_path": ["name_qualifier"],
            "legal_subject_claim_path": ["legalSubjectID"],
            "acting_subject_claim_path": ["actingSubjectID"],
        },
    },
    OIDC_DIGID_MACHTIGEN_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": DigiDAssuranceLevels.middle,
            "value_mapping": [],
        },
        "identity_settings": {
            "representee_bsn_claim_path": ["aanvrager.bsn"],
            "authorizee_bsn_claim_path": ["gemachtigde.bsn"],
            "mandate_service_id_claim_path": ["service_id"],
        },
    },
    OIDC_EH_BEWINDVOERING_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": AssuranceLevels.low_plus,
            "value_mapping": [],
        },
        "identity_settings": {
            "identifier_type_claim_path": ["name_qualifier"],
            "legal_subject_claim_path": ["aanvrager.kvk"],
            "acting_subject_claim_path": ["actingSubjectID"],
            "representee_claim_path": ["representeeBSN"],
            "mandate_service_id_claim_path": ["service_id"],
            "mandate_service_uuid_claim_path": ["service_uuid"],
        },
    },
    OIDC_ORG_IDENTIFIER: {
        "user_settings": {
            "claim_mappings": {
                "username": ["preferred_username"],
                "email": ["email"],
                "employee_id": ["employeeId"],
            },
            "username_case_sensitive": True,
            "sensitive_claims": [],
        },
        "groups_settings": {
            "claim_mapping": ["groups"],
            "sync": True,
            "sync_pattern": "*",
            "make_users_staff": False,
            "superuser_group_names": [],
            "default_groups": [],
        },
    },
}
CLIENT_DEFAULT_SCOPES = {
    OIDC_DIGID_IDENTIFIER: ["openid", "bsn"],
    OIDC_DIGID_MACHTIGEN_IDENTIFIER: ["openid", "bsn"],
    OIDC_EH_IDENTIFIER: ["openid", "kvk"],
    OIDC_EH_BEWINDVOERING_IDENTIFIER: ["openid", "bsn"],
    OIDC_ADMIN_CONFIG_IDENTIFIER: ["email", "profile", "openid"],
    OIDC_ORG_IDENTIFIER: ["openid", "email", "profile", "employeeId"],
}


def make_client(
    identifier: str, provider: OIDCProvider, overrides: JSONObject | None = None
) -> OIDCClient:
    defaults = {
        "enabled": True,
        "oidc_rp_client_id": "testid",
        "oidc_rp_client_secret": "7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I",
        "oidc_rp_sign_algo": "RS256",
        "oidc_rp_scopes_list": copy.deepcopy(CLIENT_DEFAULT_SCOPES[identifier]),
        "oidc_provider": provider,
        "options": copy.deepcopy(CLIENT_DEFAULT_OPTIONS[identifier]),
    }
    if overrides:
        for override_path, override_value in overrides.items():
            assign(defaults, override_path, override_value)

    client, _ = OIDCClient.objects.update_or_create(
        identifier=identifier,
        defaults=defaults,
    )
    return client
