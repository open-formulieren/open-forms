"""
Keycloak helpers taken from mozilla-django-oidc-db::tests/utils.py & pytest fixtures.

These help dealing with/stubbing out OpenID Provider configuration.

The Keycloak client ID/secret and URLs are set up for the config in
docker/docker-compose.keycloak.yml. See the README.md in docker/keycloak/ for more
information.
"""

import copy
from contextlib import contextmanager, nullcontext
from unittest.mock import patch

from django.apps import apps

import faker
from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from glom import assign
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.tests.factories import (
    OIDCProviderFactory,
)
from pyquery import PyQuery as pq
from requests import Session

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
from openforms.typing import JSONObject

KEYCLOAK_BASE_URL = "http://localhost:8080/realms/test/protocol/openid-connect"


def keycloak_login(
    login_url: str,
    username: str = "testuser",
    password: str = "testuser",
    host: str = "http://testserver/",
    session: Session | None = None,
) -> str:
    """
    Test helper to perform a keycloak login.

    :param login_url: A login URL for keycloak with all query string parameters. E.g.
        `client.get(reverse("login"))["Location"]`.
    :returns: The redirect URI to consume in the django application, with the ``code``
        ``state`` query parameters. Consume this with ``response = client.get(url)``.
    """
    cm = Session() if session is None else nullcontext(session)
    with cm as session:
        login_page = session.get(login_url)
        assert login_page.status_code == 200

        # process keycloak's login form and submit the username + password to
        # authenticate
        document = pq(login_page.text)
        login_form = document("form#kc-form-login")
        submit_url = login_form.attr("action")
        assert isinstance(submit_url, str)
        login_response = session.post(
            submit_url,
            data={
                "username": username,
                "password": password,
                "credentialId": "",
                "login": "Sign In",
            },
            allow_redirects=False,
        )

        assert login_response.status_code == 302
        assert (redirect_uri := login_response.headers["Location"]).startswith(host)

        return redirect_uri


@contextmanager
def mock_oidc_db_config(app_label: str, model: str, **overrides):
    """
    Bundle all the required mocks.

    This context manager deliberately prevents the mocked things from being injected in
    the test method signature.
    """
    defaults = {
        "enabled": True,
        "oidc_rp_client_id": "testid",
        "oidc_rp_client_secret": "7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I",
        "oidc_rp_sign_algo": "RS256",
        "oidc_rp_scopes_list": ["openid"],
        "oidc_op_jwks_endpoint": f"{KEYCLOAK_BASE_URL}/certs",
        "oidc_op_authorization_endpoint": f"{KEYCLOAK_BASE_URL}/auth",
        "oidc_op_token_endpoint": f"{KEYCLOAK_BASE_URL}/token",
        "oidc_op_user_endpoint": f"{KEYCLOAK_BASE_URL}/userinfo",
    }
    field_values = {**defaults, **overrides}
    model_cls = apps.get_model(app_label, model)
    with (
        # bypass django-solo queries + cache hits
        patch(
            f"{model_cls.__module__}.{model}.get_solo",
            return_value=model_cls(**field_values),
        ),
        # mock the state & nonce random value generation so we get predictable URLs to
        # match with VCR
        patch(
            "mozilla_django_oidc.views.get_random_string",
            return_value="not-a-random-string",
        ),
    ):
        yield


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
    OIDC_EIDAS_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": EIDASAssuranceLevels.low,
            "value_mapping": [],
        },
        "identity_settings": {
            "legal_subject_identifier_claim_path": ["person_identifier"],
            "legal_subject_identifier_type_claim_path": ["person_identifier_type"],
            "legal_subject_first_name_claim_path": ["first_name"],
            "legal_subject_family_name_claim_path": ["family_name"],
            "legal_subject_date_of_birth_claim_path": ["birthdate"],
        },
    },
    OIDC_EIDAS_COMPANY_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": EIDASAssuranceLevels.low,
            "value_mapping": [],
        },
        "identity_settings": {
            "legal_subject_identifier_claim_path": ["company_identifier"],
            "legal_subject_name_claim_path": ["company_name"],
            "acting_subject_identifier_claim_path": ["person_identifier"],
            "acting_subject_identifier_type_claim_path": ["person_identifier_type"],
            "acting_subject_first_name_claim_path": ["first_name"],
            "acting_subject_family_name_claim_path": ["family_name"],
            "acting_subject_date_of_birth_claim_path": ["birthdate"],
            "mandate_service_id_claim_path": ["service_id"],
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
    OIDC_YIVI_IDENTIFIER: {
        "loa_settings": {
            "claim_path": ["authsp_level"],
            "default": AssuranceLevels.low_plus,
            "value_mapping": [],
        },
        "identity_settings": {
            "bsn_claim_path": ["bsn"],
            "bsn_loa_claim_path": [],
            "bsn_default_loa": "",
            "bsn_loa_value_mapping": [],
            "kvk_claim_path": ["kvk"],
            "kvk_loa_claim_path": [],
            "kvk_default_loa": "",
            "kvk_loa_value_mapping": [],
            "pseudo_claim_path": ["pbdf.sidn-pbdf.irma.pseudonym"],
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
    OIDC_EIDAS_IDENTIFIER: ["openid", "eidas"],
    OIDC_EIDAS_COMPANY_IDENTIFIER: ["openid", "eidas"],
    OIDC_YIVI_IDENTIFIER: ["openid"],
}


@contextmanager
def mock_oidc_client(
    identifier: str,
    *,
    provider_identifier: str = "",
    overrides: JSONObject | None = None,
    provider_overrides: JSONObject | None = None,
):
    provider_data = {
        "oidc_op_jwks_endpoint": f"{KEYCLOAK_BASE_URL}/certs",
        "oidc_op_authorization_endpoint": f"{KEYCLOAK_BASE_URL}/auth",
        "oidc_op_token_endpoint": f"{KEYCLOAK_BASE_URL}/token",
        "oidc_op_user_endpoint": f"{KEYCLOAK_BASE_URL}/userinfo",
        "oidc_op_logout_endpoint": f"{KEYCLOAK_BASE_URL}/logout",
    }
    if provider_overrides:
        provider_data = {
            "identifier": provider_identifier,
            **provider_data,
            **provider_overrides,
        }

    if not provider_identifier:
        fake = faker.Faker()
        provider_data["identifier"] = fake.slug()

    provider = OIDCProviderFactory.create(**provider_data)

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

    client = OIDCClient(
        identifier=identifier,
        **defaults,
    )
    with (
        patch(
            "mozilla_django_oidc_db.models.OIDCClient.objects.get", return_value=client
        ),
        patch(
            "mozilla_django_oidc_db.models.OIDCClient.objects.resolve",
            return_value=client,
        ),
    ):
        yield


@contextmanager
def mock_get_random_string():
    """Mock the state & nonce random value generation

    Needed so that we get predictable URLs to match with VCR.
    """
    with patch(
        "mozilla_django_oidc.views.get_random_string",
        return_value="not-a-random-string",
    ):
        yield


class KeycloakProviderMixin:
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.provider = OIDCProviderFactory.create(
            identifier="keycloak-provider",
            oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
            oidc_op_authorization_endpoint=f"{KEYCLOAK_BASE_URL}/auth",
            oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
            oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
            oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
        )
