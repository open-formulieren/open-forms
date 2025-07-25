import base64
import json
import re

from django.urls.base import reverse_lazy

from furl import furl

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.oidc_plugins.constants import (
    OIDC_YIVI_IDENTIFIER,
)
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.authentication.tests.utils import URLsHelper
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import mock_get_random_string, mock_oidc_client

from .base import IntegrationTestsBase


class YiviInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based Yivi authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def assertCondisconScope(self, scope: str, expected: list[list[list[str]]]):
        # Fetch the signicat param part of the scope
        match = re.search(r"(signicat:param:[^\s]+)", scope)
        signicat_scope = match.group(1) if match else None

        assert signicat_scope is not None

        base64_part = signicat_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(condiscon, expected)

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={"options.identity_settings.pseudo_claim_path": ["attribute.pseudo"]},
    )
    def test_start_flow_redirects_to_oidc_provider(self):
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [],
                "additional_attributes_groups": [],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        self.assertEqual(redirect_target.host, "localhost")
        self.assertEqual(redirect_target.port, 8080)
        self.assertEqual(
            redirect_target.path,
            "/realms/test/protocol/openid-connect/auth",
        )
        scope_list = query_params["scope"].split(" ")
        self.assertIn("openid", scope_list)
        self.assertCondisconScope(
            query_params["scope"],
            [
                [
                    ["attribute.pseudo"],
                ],
            ],
        )
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={"options.identity_settings.bsn_claim_path": ["attribute.bsn"]},
    )
    def test_signicat_condiscon_contains_only_the_chosen_authentication_and_additional_attributes(
        self,
    ):
        AttributeGroupFactory(name="personal", attributes=["first_name", "last_name"])
        AttributeGroupFactory(name="mail", attributes=["email_address"])
        AttributeGroupFactory(name="phone", attributes=["phone_number"])
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": ["personal", "mail"],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")
        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        scope_list = query_params["scope"].split(" ")
        self.assertIn("openid", scope_list)
        self.assertCondisconScope(
            query_params["scope"],
            [
                # The `bsn_claim` from the Yivi global config. This is required.
                [
                    ["attribute.bsn"],
                ],
                # The chosen `additional_attributes_groups`.
                # These are, per group, optional.
                [["first_name", "last_name"], []],
                [["email_address"], []],
            ],
        )

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["attribute.bsn"],
            "options.loa_settings.bsn_loa_claim_path": ["attribute.loa:bsn"],
        },
    )
    def test_signicat_condiscon_authentication_attributes_also_contain_defined_loa(
        self,
    ):
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")
        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        scope_list = query_params["scope"].split(" ")
        self.assertIn("openid", scope_list)
        self.assertCondisconScope(
            query_params["scope"],
            [
                # The ``bsn_claim`` and ``bsn_loa_claim`` from the Yivi global config.
                [
                    ["attribute.bsn", "attribute.loa:bsn"],
                ],
            ],
        )

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["attribute.bsn"],
            "options.identity_settings.kvk_claim_path": ["attribute.kvk"],
            "options.identity_settings.pseudo_claim_path": ["attribute.pseudo"],
        },
    )
    def test_signicat_condiscon_contains_multiple_chosen_authentication_attributes(
        self,
    ):
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [
                    AuthAttribute.bsn,
                    AuthAttribute.kvk,
                    AuthAttribute.pseudo,
                ],
                "additional_attributes_groups": [],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")
        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        scope_list = query_params["scope"].split(" ")
        self.assertIn("openid", scope_list)
        self.assertCondisconScope(
            query_params["scope"],
            [
                # The `bsn_claim`, `kvk_claim` and `pseudo_claim` from the Yivi global
                # config. The user can choose which one they want to provide.
                [
                    ["attribute.bsn"],
                    ["attribute.kvk"],
                    ["attribute.pseudo"],
                ],
            ],
        )

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.pseudo_claim_path": ["attribute.pseudo"],
        },
    )
    def test_signicat_condiscon_without_pre_defined_attributes_contains_the_pseudo_claim(
        self,
    ):
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [],
                "additional_attributes_groups": [],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")
        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        scope_list = query_params["scope"].split(" ")
        self.assertIn("openid", scope_list)
        self.assertCondisconScope(
            query_params["scope"],
            [
                [
                    ["attribute.pseudo"],
                ],
            ],
        )
