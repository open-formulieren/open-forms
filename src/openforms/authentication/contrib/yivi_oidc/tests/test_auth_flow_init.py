import base64
import json
import re

from django.urls.base import reverse_lazy

from furl import furl

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.tests.base import mock_yivi_config
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.authentication.tests.utils import URLsHelper
from openforms.forms.tests.factories import FormFactory

from ..models import YiviOpenIDConnectConfig
from .base import IntegrationTestsBase


class YiviInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based Yivi authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def _assert_condiscon_scope(self, scope: str, expected: list[list[list[str]]]):
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

    @mock_yivi_config(pseudo_claim=["attribute.pseudo"])
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
        self.assertEqual(
            query_params["scope"],
            ("openid signicat:param:condiscon_base64:W1tbImF0dHJpYnV0ZS5wc2V1ZG8iXV1d"),
        )
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_yivi_config(bsn_claim=["attribute.bsn"])
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

        self.assertEqual(
            query_params["scope"],
            (
                "openid "
                "signicat:param:condiscon_base64:"
                "W1tbImF0dHJpYnV0ZS5ic24iXV0sIFtbImZpcnN0X25hbWUiLCAibGFzdF9u"
                "YW1lIl0sIFtdXSwgW1siZW1haWxfYWRkcmVzcyJdLCBbXV1d"
            ),
        )
        self._assert_condiscon_scope(
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

    @mock_yivi_config(bsn_claim=["attribute.bsn"], bsn_loa_claim=["attribute.loa:bsn"])
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

        # Sanity check, Yivi config didn't change
        yivi_global_config = YiviOpenIDConnectConfig.get_solo()
        self.assertEqual(yivi_global_config.bsn_claim, ["attribute.bsn"])
        self.assertEqual(yivi_global_config.bsn_loa_claim, ["attribute.loa:bsn"])

        self.assertEqual(
            query_params["scope"],
            (
                "openid "
                "signicat:param:condiscon_base64:"
                "W1tbImF0dHJpYnV0ZS5ic24iLCAiYXR0cmlidXRlLmxvYTpic24iXV1d"
            ),
        )
        self._assert_condiscon_scope(
            query_params["scope"],
            [
                # The ``bsn_claim`` and ``bsn_loa_claim`` from the Yivi global config.
                [
                    ["attribute.bsn", "attribute.loa:bsn"],
                ],
            ],
        )

    @mock_yivi_config(
        bsn_claim=["attribute.bsn"],
        kvk_claim=["attribute.kvk"],
        pseudo_claim=["attribute.pseudo"],
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

        self.assertEqual(
            query_params["scope"],
            (
                "openid "
                "signicat:param:condiscon_base64:"
                "W1tbImF0dHJpYnV0ZS5ic24iXSwgWyJhdHRyaWJ1dGUua3ZrIl0s"
                "IFsiYXR0cmlidXRlLnBzZXVkbyJdXV0="
            ),
        )
        self._assert_condiscon_scope(
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

    @mock_yivi_config(pseudo_claim=["attribute.pseudo"])
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

        self.assertEqual(
            query_params["scope"],
            ("openid signicat:param:condiscon_base64:W1tbImF0dHJpYnV0ZS5wc2V1ZG8iXV1d"),
        )
        self._assert_condiscon_scope(
            query_params["scope"],
            [
                [
                    ["attribute.pseudo"],
                ],
            ],
        )
