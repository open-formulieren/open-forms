from functools import partial
from pathlib import Path

from django.test import override_settings

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from django_webtest import WebTest

from openforms.authentication.contrib.digid_eherkenning_oidc.choices import (
    EIDASAssuranceLevels,
)
from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL, mock_oidc_db_config
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "data").resolve()


def mock_config(model: str, **overrides):
    overrides.setdefault("oidc_op_logout_endpoint", f"{KEYCLOAK_BASE_URL}/logout")
    return mock_oidc_db_config(
        app_label="digid_eherkenning_oidc", model=model, **overrides
    )


mock_digid_config = partial(
    mock_config,
    model="OFDigiDConfig",
    oidc_rp_scopes_list=["openid", "bsn"],
    loa_claim=["authsp_level"],
    default_loa=DigiDAssuranceLevels.middle,
)

mock_eidas_config = partial(
    mock_config,
    model="OFEIDASConfig",
    oidc_rp_scopes_list=["openid", "eidas"],
    loa_claim=["authsp_level"],
    legal_subject_identifier_claim=["person_identifier"],
    legal_subject_identifier_type_claim=["person_identifier_type"],
    legal_subject_first_name_claim=["first_name"],
    legal_subject_family_name_claim=["family_name"],
    legal_subject_date_of_birth_claim=["birthdate"],
    default_loa=EIDASAssuranceLevels.low,
)

mock_eidas_company_config = partial(
    mock_config,
    model="OFEIDASCompanyConfig",
    oidc_rp_scopes_list=["openid", "eidas"],
    loa_claim=["authsp_level"],
    legal_subject_identifier_claim=["company_identifier"],
    legal_subject_name_claim=["company_name"],
    acting_subject_identifier_claim=["person_identifier"],
    acting_subject_identifier_type_claim=["person_identifier_type"],
    acting_subject_first_name_claim=["first_name"],
    acting_subject_family_name_claim=["family_name"],
    acting_subject_date_of_birth_claim=["birthdate"],
    mandate_service_id_claim=["service_id"],
    default_loa=EIDASAssuranceLevels.low,
)

mock_eherkenning_config = partial(
    mock_config,
    model="OFEHerkenningConfig",
    oidc_rp_scopes_list=["openid", "kvk"],
    identifier_type_claim=["name_qualifier"],
    legal_subject_claim=["legalSubjectID"],
    acting_subject_claim=["actingSubjectID"],
    branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
    loa_claim=["authsp_level"],
    default_loa=AssuranceLevels.low_plus,
)

mock_digid_machtigen_config = partial(
    mock_config,
    model="OFDigiDMachtigenConfig",
    oidc_rp_scopes_list=["openid", "bsn"],
    representee_bsn_claim=["aanvrager.bsn"],
    authorizee_bsn_claim=["gemachtigde.bsn"],
    mandate_service_id_claim=["service_id"],
    loa_claim=["authsp_level"],
    default_loa=DigiDAssuranceLevels.middle,
)

mock_eherkenning_bewindvoering_config = partial(
    mock_config,
    model="OFEHerkenningBewindvoeringConfig",
    oidc_rp_scopes_list=["openid", "bsn"],
    identifier_type_claim=["name_qualifier"],
    legal_subject_claim=["legalSubjectID"],
    acting_subject_claim=["actingSubjectID"],
    branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
    representee_claim=["representeeBSN"],
    mandate_service_id_claim=["service_id"],
    mandate_service_uuid_claim=["service_uuid"],
    loa_claim=["authsp_level"],
    default_loa=AssuranceLevels.low_plus,
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class IntegrationTestsBase(OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES
