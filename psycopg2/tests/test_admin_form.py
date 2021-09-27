from json.decoder import JSONDecodeError
from unittest.mock import patch

from django.utils.translation import gettext as _

import pytest
import requests_mock
from requests import Response
from requests.exceptions import RequestException

from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm
from mozilla_django_oidc_db.models import OpenIDConnectConfig, get_claim_mapping


@pytest.mark.django_db
def test_derive_endpoints_success():
    form_data = {
        "oidc_rp_client_id": "clientid",
        "oidc_rp_client_secret": "secret",
        "oidc_rp_sign_algo": "RS256",
        "oidc_op_discovery_endpoint": "http://discovery-endpoint.nl/",
        "claim_mapping": get_claim_mapping(),
        "groups_claim": "roles",
    }
    form = OpenIDConnectConfigForm(data=form_data)

    configuration = {
        "authorization_endpoint": "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
        "token_endpoint": "http://provider.com/auth/realms/master/protocol/openid-connect/token",
        "userinfo_endpoint": "http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
        "jwks_uri": "http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    }
    with requests_mock.Mocker() as m:
        m.get(
            "http://discovery-endpoint.nl/.well-known/openid-configuration",
            json=configuration,
        )
        assert form.is_valid()

    config = form.save()
    assert (
        config.oidc_op_authorization_endpoint
        == "http://provider.com/auth/realms/master/protocol/openid-connect/auth"
    )
    assert (
        config.oidc_op_token_endpoint
        == "http://provider.com/auth/realms/master/protocol/openid-connect/token"
    )
    assert (
        config.oidc_op_user_endpoint
        == "http://provider.com/auth/realms/master/protocol/openid-connect/userinfo"
    )
    assert (
        config.oidc_op_jwks_endpoint
        == "http://provider.com/auth/realms/master/protocol/openid-connect/certs"
    )


@patch("requests.get", side_effect=RequestException)
def test_derive_endpoints_request_error(*m):
    form_data = {
        "oidc_rp_client_id": "clientid",
        "oidc_rp_client_secret": "secret",
        "oidc_rp_sign_algo": "RS256",
        "oidc_op_discovery_endpoint": "http://discovery-endpoint.nl",
        "claim_mapping": get_claim_mapping(),
        "groups_claim": "roles",
    }
    form = OpenIDConnectConfigForm(data=form_data)

    form.is_valid()

    assert form.errors == {
        "oidc_op_discovery_endpoint": [
            _("Something went wrong while retrieving the configuration.")
        ]
    }


@patch("requests.get", side_effect=JSONDecodeError("error", "test", 1))
def test_derive_endpoints_json_error(*m):
    form_data = {
        "oidc_rp_client_id": "clientid",
        "oidc_rp_client_secret": "secret",
        "oidc_rp_sign_algo": "RS256",
        "oidc_op_discovery_endpoint": "http://discovery-endpoint.nl",
        "claim_mapping": get_claim_mapping(),
        "groups_claim": "roles",
    }
    form = OpenIDConnectConfigForm(data=form_data)

    form.is_valid()

    assert form.errors == {
        "oidc_op_discovery_endpoint": [
            _("Something went wrong while retrieving the configuration.")
        ]
    }


def test_no_discovery_endpoint_other_fields_required():
    form_data = {
        "oidc_rp_client_id": "clientid",
        "oidc_rp_client_secret": "secret",
        "oidc_rp_sign_algo": "RS256",
        "claim_mapping": get_claim_mapping(),
        "groups_claim": "roles",
    }
    form = OpenIDConnectConfigForm(data=form_data)

    form.is_valid()

    assert form.errors == {
        "oidc_op_authorization_endpoint": [_("This field is required.")],
        "oidc_op_token_endpoint": [_("This field is required.")],
        "oidc_op_user_endpoint": [_("This field is required.")],
    }
