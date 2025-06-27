from functools import partial

from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL, mock_oidc_db_config


def mock_config(model: str, **overrides):
    overrides.setdefault("oidc_op_logout_endpoint", f"{KEYCLOAK_BASE_URL}/logout")
    return mock_oidc_db_config(app_label="yivi_oidc", model=model, **overrides)


mock_yivi_config = partial(
    mock_config,
    model="YiviOpenIDConnectConfig",
    oidc_rp_scopes_list=["openid"],
)
