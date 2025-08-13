import factory
from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.tests.factories import (
    OIDCClientFactory,
    OIDCProviderFactory,
)

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
    EIDASAssuranceLevels,
)
from openforms.authentication.contrib.org_oidc.oidc_plugins.constants import (
    OIDC_ORG_IDENTIFIER,
)
from openforms.authentication.contrib.yivi_oidc.oidc_plugins.constants import (
    OIDC_YIVI_IDENTIFIER,
)
from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL


class OFOIDCClientFactory(OIDCClientFactory):
    enabled = True

    class Params:  # pyright: ignore[reportIncompatibleVariableOverride]
        with_keycloak_provider = factory.Trait(
            oidc_provider=factory.SubFactory(
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
        with_admin = factory.Trait(
            identifier=OIDC_ADMIN_CONFIG_IDENTIFIER,
            oidc_rp_scopes_list=["email", "profile", "openid"],
            options=factory.Dict(
                {
                    "user_settings": factory.Dict(
                        {
                            "claim_mappings": factory.Dict(
                                {
                                    "username": ["sub"],
                                    "first_name": [],
                                    "last_name": [],
                                    "email": [],
                                }
                            ),
                            "username_case_sensitive": True,
                            "sensitive_claims": [],
                        }
                    ),
                    "groups_settings": factory.Dict(
                        {
                            "claim_mapping": ["groups"],
                            "sync": True,
                            "sync_pattern": "*",
                            "make_users_staff": False,
                            "superuser_group_names": [],
                            "default_groups": [],
                        }
                    ),
                }
            ),
        )
        with_org = factory.Trait(
            identifier=OIDC_ORG_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "email", "profile", "employeeId"],
            options=factory.Dict(
                {
                    "user_settings": factory.Dict(
                        {
                            "claim_mappings": factory.Dict(
                                {
                                    "username": ["preferred_username"],
                                    "email": ["email"],
                                    "employee_id": ["employeeId"],
                                }
                            ),
                            "username_case_sensitive": True,
                            "sensitive_claims": [],
                        }
                    ),
                    "groups_settings": factory.Dict(
                        {
                            "claim_mapping": ["groups"],
                            "sync": True,
                            "sync_pattern": "*",
                            "make_users_staff": False,
                            "superuser_group_names": [],
                            "default_groups": [],
                        }
                    ),
                }
            ),
        )
        with_digid = factory.Trait(
            identifier=OIDC_DIGID_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "bsn"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": DigiDAssuranceLevels.middle,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "bsn_claim_path": ["bsn"],
                        }
                    ),
                }
            ),
        )
        with_digid_machtigen = factory.Trait(
            identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "bsn"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": DigiDAssuranceLevels.middle,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "representee_bsn_claim_path": ["aanvrager.bsn"],
                            "authorizee_bsn_claim_path": ["gemachtigde.bsn"],
                            "mandate_service_id_claim_path": ["service_id"],
                        }
                    ),
                }
            ),
        )
        with_eherkenning = factory.Trait(
            identifier=OIDC_EH_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "kvk"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": AssuranceLevels.low_plus,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "identifier_type_claim_path": ["name_qualifier"],
                            "legal_subject_claim_path": ["legalSubjectID"],
                            "acting_subject_claim_path": ["actingSubjectID"],
                        }
                    ),
                }
            ),
        )
        with_eherkenning_bewindvoering = factory.Trait(
            identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "bsn"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": AssuranceLevels.low_plus,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "identifier_type_claim_path": ["name_qualifier"],
                            "legal_subject_claim_path": ["aanvrager.kvk"],
                            "acting_subject_claim_path": ["actingSubjectID"],
                            "representee_claim_path": ["representeeBSN"],
                            "mandate_service_id_claim_path": ["service_id"],
                            "mandate_service_uuid_claim_path": ["service_uuid"],
                        }
                    ),
                }
            ),
        )
        with_eidas = factory.Trait(
            identifier=OIDC_EIDAS_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "eidas"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": EIDASAssuranceLevels.low,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "legal_subject_identifier_claim_path": [
                                "person_identifier"
                            ],
                            "legal_subject_identifier_type_claim_path": [
                                "person_identifier_type"
                            ],
                            "legal_subject_first_name_claim_path": ["first_name"],
                            "legal_subject_family_name_claim_path": ["family_name"],
                            "legal_subject_date_of_birth_claim_path": ["birthdate"],
                        }
                    ),
                }
            ),
        )
        with_eidas_company = factory.Trait(
            identifier=OIDC_EIDAS_COMPANY_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "eidas"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "claim_path": ["authsp_level"],
                            "default": EIDASAssuranceLevels.low,
                            "value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "legal_subject_identifier_claim_path": [
                                "company_identifier"
                            ],
                            "legal_subject_name_claim_path": ["company_name"],
                            "acting_subject_identifier_claim_path": [
                                "person_identifier"
                            ],
                            "acting_subject_identifier_type_claim_path": [
                                "person_identifier_type"
                            ],
                            "acting_subject_first_name_claim_path": ["first_name"],
                            "acting_subject_family_name_claim_path": ["family_name"],
                            "acting_subject_date_of_birth_claim_path": ["birthdate"],
                            "mandate_service_id_claim_path": ["service_id"],
                        }
                    ),
                }
            ),
        )
        with_yivi = factory.Trait(
            identifier=OIDC_YIVI_IDENTIFIER,
            oidc_rp_scopes_list=["openid"],
            options=factory.Dict(
                {
                    "loa_settings": factory.Dict(
                        {
                            "bsn_loa_claim_path": [],
                            "bsn_default_loa": "",
                            "bsn_loa_value_mapping": [],
                            "kvk_loa_claim_path": [],
                            "kvk_default_loa": "",
                            "kvk_loa_value_mapping": [],
                        }
                    ),
                    "identity_settings": factory.Dict(
                        {
                            "bsn_claim_path": ["bsn"],
                            "kvk_claim_path": ["kvk"],
                            "pseudo_claim_path": ["pbdf.sidn-pbdf.irma.pseudonym"],
                        }
                    ),
                }
            ),
        )
