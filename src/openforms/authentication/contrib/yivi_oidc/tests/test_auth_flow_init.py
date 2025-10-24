import base64
import json
import re

from django.urls.base import reverse_lazy

from furl import furl

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.forms.tests.factories import FormFactory

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

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_yivi=True,
            options__identity_settings__pseudo_claim_path=["attribute.pseudo"],
        )
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
        scope = query_params["scope"]
        assert scope is not None
        self.assertIn("openid", scope.split(" "))
        self.assertCondisconScope(
            scope,
            [
                [
                    ["attribute.pseudo"],
                ],
            ],
        )
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    def test_signicat_condiscon_contains_only_the_chosen_authentication_and_additional_attributes(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["attribute.bsn"],
        )
        AttributeGroupFactory.create(
            name="personal",
            uuid="e90c2d3e-4ee2-4590-ab10-206d1a438293",
            attributes=["first_name", "last_name"],
        )
        AttributeGroupFactory.create(
            name="mail",
            uuid="7b083f26-74dc-49ea-9794-60e3e6e71c1c",
            attributes=["email_address"],
        )
        # This `phone` group is defined, but isn't used in the form
        AttributeGroupFactory.create(
            name="phone",
            uuid="7cca8de0-bbaa-49bc-bd22-c07cb331ff3a",
            attributes=["phone_number"],
        )
        form = FormFactory.create(
            authentication_backend="yivi_oidc",
            authentication_backend__options={
                "authentication_options": [AuthAttribute.bsn],
                "additional_attributes_groups": [
                    # The uuids of the `personal` and `mail` attributegroups
                    "e90c2d3e-4ee2-4590-ab10-206d1a438293",
                    "7b083f26-74dc-49ea-9794-60e3e6e71c1c",
                ],
            },
        )
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="yivi_oidc")
        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params

        scope = query_params["scope"]
        assert scope is not None
        self.assertIn("openid", scope.split(" "))
        self.assertCondisconScope(
            scope,
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

    def test_signicat_condiscon_authentication_attributes_also_contain_defined_loa(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["attribute.bsn"],
            options__loa_settings__bsn_loa_claim_path=["attribute.loa:bsn"],
        )
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

        scope = query_params["scope"]
        assert scope is not None
        self.assertIn("openid", scope.split(" "))
        self.assertCondisconScope(
            scope,
            [
                # The ``bsn_claim`` and ``bsn_loa_claim`` from the Yivi global config.
                [
                    ["attribute.bsn", "attribute.loa:bsn"],
                ],
            ],
        )

    def test_signicat_condiscon_contains_multiple_chosen_authentication_attributes(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["attribute.bsn"],
            options__identity_settings__kvk_claim_path=["attribute.kvk"],
            options__identity_settings__pseudo_claim_path=["attribute.pseudo"],
        )
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

        scope = query_params["scope"]
        assert scope is not None
        self.assertIn("openid", scope.split(" "))
        self.assertCondisconScope(
            scope,
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

    def test_signicat_condiscon_without_pre_defined_attributes_contains_the_pseudo_claim(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_yivi=True,
            options__identity_settings__pseudo_claim_path=["attribute.pseudo"],
        )
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

        scope = query_params["scope"]
        assert scope is not None
        self.assertIn("openid", scope.split(" "))
        self.assertCondisconScope(
            scope,
            [
                [
                    ["attribute.pseudo"],
                ],
            ],
        )
