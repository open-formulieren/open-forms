from functools import partial
from pathlib import Path

from django.test import override_settings

from django_webtest import WebTest

from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL, mock_oidc_db_config
from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "data").resolve()


def mock_config(model: str, **overrides):
    overrides.setdefault("oidc_op_logout_endpoint", f"{KEYCLOAK_BASE_URL}/logout")
    return mock_oidc_db_config(app_label="yivi_oidc", model=model, **overrides)


mock_yivi_config = partial(
    mock_config,
    model="YiviOpenIDConnectConfig",
    oidc_rp_scopes_list=["openid"],
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class IntegrationTestsBase(OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES
