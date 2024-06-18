from functools import partial
from pathlib import Path

from django.test import override_settings

from django_webtest import WebTest

from openforms.utils.tests.keycloak import mock_oidc_db_config
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "data").resolve()


mock_org_oidc_config = partial(
    mock_oidc_db_config,
    app_label="authentication_org_oidc",
    model="OrgOpenIDConnectConfig",
    id=1,  # required for the group queries because we're using in-memory objects
    oidc_rp_scopes_list=["openid", "email", "profile"],
    username_claim=["preferred_username"],
    claim_mapping={
        "email": ["email"],
        "employee_id": ["preferred_username"],
    },
    groups_claim=["groups"],
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class IntegrationTestsBase(OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES
