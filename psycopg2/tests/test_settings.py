import pytest

from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.middleware import SessionRefresh
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from mozilla_django_oidc_db.views import OIDCAuthenticationRequestView


@pytest.mark.django_db
def test_backend_settings_derived_from_model_oidc_not_enabled():
    config = OpenIDConnectConfig.get_solo()
    config.enabled = False
    config.save()

    backend = OIDCAuthenticationBackend()

    # verify that the settings are not set (because of early return in __init__)
    assert not hasattr(backend, "OIDC_RP_CLIENT_ID")
    assert not hasattr(backend, "OIDC_RP_CLIENT_SECRET")
    assert not hasattr(backend, "OIDC_RP_SIGN_ALGO")
    assert not hasattr(backend, "OIDC_OP_JWKS_ENDPOINT")
    assert not hasattr(backend, "OIDC_OP_TOKEN_ENDPOINT")
    assert not hasattr(backend, "OIDC_OP_USER_ENDPOINT")
    assert not hasattr(backend, "OIDC_RP_IDP_SIGN_KEY")


@pytest.mark.django_db
def test_backend_settings_derived_from_model_oidc_enabled():
    config = OpenIDConnectConfig.get_solo()

    config.enabled = True
    config.oidc_rp_client_id = "testid"
    config.oidc_rp_client_secret = "secret"
    config.oidc_rp_sign_algo = "HS256"
    config.oidc_rp_scopes_list = ["openid", "email"]
    config.oidc_op_jwks_endpoint = "http://some.endpoint/v1/jwks"
    config.oidc_op_authorization_endpoint = "http://some.endpoint/v1/auth"
    config.oidc_op_token_endpoint = "http://some.endpoint/v1/token"
    config.oidc_op_user_endpoint = "http://some.endpoint/v1/user"

    config.save()

    backend = OIDCAuthenticationBackend()

    # verify that the settings are derived from OpenIDConnectConfig
    assert backend.OIDC_RP_CLIENT_ID == "testid"
    assert backend.OIDC_RP_CLIENT_SECRET == "secret"
    assert backend.OIDC_RP_SIGN_ALGO == "HS256"
    assert backend.OIDC_OP_JWKS_ENDPOINT == "http://some.endpoint/v1/jwks"
    assert backend.OIDC_OP_TOKEN_ENDPOINT == "http://some.endpoint/v1/token"
    assert backend.OIDC_OP_USER_ENDPOINT == "http://some.endpoint/v1/user"
    assert backend.OIDC_RP_IDP_SIGN_KEY is None


@pytest.mark.django_db
def test_view_settings_derived_from_model_oidc_enabled():
    config = OpenIDConnectConfig.get_solo()

    config.enabled = True
    config.oidc_rp_client_id = "testid"
    config.oidc_rp_client_secret = "secret"
    config.oidc_rp_sign_algo = "HS256"
    config.oidc_rp_scopes_list = ["openid", "email"]
    config.oidc_op_jwks_endpoint = "http://some.endpoint/v1/jwks"
    config.oidc_op_authorization_endpoint = "http://some.endpoint/v1/auth"
    config.oidc_op_token_endpoint = "http://some.endpoint/v1/token"
    config.oidc_op_user_endpoint = "http://some.endpoint/v1/user"

    config.save()

    view = OIDCAuthenticationRequestView()

    # verify that the settings are derived from OpenIDConnectConfig
    assert view.OIDC_RP_CLIENT_ID == "testid"
    assert view.OIDC_OP_AUTH_ENDPOINT == "http://some.endpoint/v1/auth"
