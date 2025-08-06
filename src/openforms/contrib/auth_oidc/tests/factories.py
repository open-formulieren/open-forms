import copy
from contextlib import contextmanager
from unittest.mock import patch

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from factory import SubFactory, Trait, post_generation
from glom import Path, assign
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.tests.factories import (
    OIDCClientFactory,
    OIDCProviderFactory,
)

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    EIDASAssuranceLevels,
)
from openforms.authentication.registry import (
    register as auth_register,
)
from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL


class OFOIDCClientFactory(OIDCClientFactory):
    enabled = True

    class Params:
        with_keycloak_provider = Trait(
            oidc_provider=SubFactory(
                OIDCProviderFactory,
                identifier="keycloak-provider",
                oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
                oidc_op_authorization_endpoint=f"{KEYCLOAK_BASE_URL}/auth",
                oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
                oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
                oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
            ),
            oidc_rp_client_id="testid",
            oidc_rp_client_secret="7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I",
            oidc_rp_sign_algo="RS256",
        )
        with_admin = Trait(
            oidc_rp_scopes_list=["email", "profile", "openid"],
            options={
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
        )
        with_org = Trait(
            oidc_rp_scopes_list=["openid", "email", "profile", "employeeId"],
            options={
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
        )
        with_digid = Trait(
            oidc_rp_scopes_list=["openid", "bsn"],
            options={
                "loa_settings": {
                    "claim_path": ["authsp_level"],
                    "default": DigiDAssuranceLevels.middle,
                    "value_mapping": [],
                },
                "identity_settings": {
                    "bsn_claim_path": ["bsn"],
                },
            },
        )
        with_digid_machtigen = Trait(
            oidc_rp_scopes_list=["openid", "bsn"],
            options={
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
        )
        with_eherkenning = Trait(
            oidc_rp_scopes_list=["openid", "kvk"],
            options={
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
        )
        with_eherkenning_bewindvoering = Trait(
            oidc_rp_scopes_list=["openid", "bsn"],
            options={
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
        )
        with_eidas = Trait(
            oidc_rp_scopes_list=["openid", "eidas"],
            options={
                "loa_settings": {
                    "claim_path": ["authsp_level"],
                    "default": EIDASAssuranceLevels.low,
                    "value_mapping": [],
                },
                "identity_settings": {
                    "legal_subject_identifier_claim_path": ["person_identifier"],
                    "legal_subject_identifier_type_claim_path": [
                        "person_identifier_type"
                    ],
                    "legal_subject_first_name_claim_path": ["first_name"],
                    "legal_subject_family_name_claim_path": ["family_name"],
                    "legal_subject_date_of_birth_claim_path": ["birthdate"],
                },
            },
        )
        with_eidas_company = Trait(
            oidc_rp_scopes_list=["openid", "eidas"],
            options={
                "loa_settings": {
                    "claim_path": ["authsp_level"],
                    "default": EIDASAssuranceLevels.low,
                    "value_mapping": [],
                },
                "identity_settings": {
                    "legal_subject_identifier_claim_path": ["company_identifier"],
                    "legal_subject_name_claim_path": ["company_name"],
                    "acting_subject_identifier_claim_path": ["person_identifier"],
                    "acting_subject_identifier_type_claim_path": [
                        "person_identifier_type"
                    ],
                    "acting_subject_first_name_claim_path": ["first_name"],
                    "acting_subject_family_name_claim_path": ["family_name"],
                    "acting_subject_date_of_birth_claim_path": ["birthdate"],
                    "mandate_service_id_claim_path": ["service_id"],
                },
            },
        )
        with_yivi = Trait(
            oidc_rp_scopes_list=["openid"],
            options={
                "loa_settings": {
                    "bsn_loa_claim_path": [],
                    "bsn_default_loa": "",
                    "bsn_loa_value_mapping": [],
                    "kvk_loa_claim_path": [],
                    "kvk_default_loa": "",
                    "kvk_loa_value_mapping": [],
                },
                "identity_settings": {
                    "bsn_claim_path": ["bsn"],
                    "kvk_claim_path": ["kvk"],
                    "pseudo_claim_path": ["pbdf.sidn-pbdf.irma.pseudonym"],
                },
            },
        )

    @post_generation
    def post(obj: OIDCClient, create: bool, extracted: bool, **kwargs) -> None:
        new_options = copy.deepcopy(obj.options)
        for key, value in kwargs.items():
            if not key.startswith("options"):
                continue

            option_path = key.split("__")[1:]
            assign(new_options, Path(*option_path), value, missing=dict)

        obj.options = new_options
        obj.save()


@contextmanager
def mock_auth_and_oidc_registers():
    with (
        patch.object(oidc_register, "_registry", new={}),
        patch.object(auth_register, "_registry", new={}),
    ):
        yield
