import base64
import json

from django.http.request import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings

from openforms.authentication.contrib.yivi_oidc.config import YiviOptions
from openforms.authentication.contrib.yivi_oidc.constants import (
    YiviAuthenticationAttributes,
)
from openforms.authentication.contrib.yivi_oidc.models import YiviOpenIDConnectConfig
from openforms.authentication.contrib.yivi_oidc.tests.base import mock_yivi_config
from openforms.authentication.contrib.yivi_oidc.views import OIDCAuthenticationInitView
from openforms.authentication.tests.factories import AttributeGroupFactory


# disable django solo cache to prevent test isolation breakage
@override_settings(SOLO_CACHE=None)
class YiviCondisconScopeTest(TestCase):
    """
    Test the _yivi_condiscon_scope method of OIDCAuthenticationInitView.
    """

    @mock_yivi_config(bsn_claim=["test.attribute.bsn"])
    def test_create_condiscon_scope_with_only_bsn_attribute(self):
        plugin_options: YiviOptions = {
            "authentication_options": [YiviAuthenticationAttributes.bsn],
            "additional_attributes_groups": [],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W1tbInRlc3QuYXR0cmlidXRlLmJzbiJdXV0=",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(condiscon, [[["test.attribute.bsn"]]])

    @mock_yivi_config(legal_subject_claim=["test.attribute.kvk"])
    def test_create_condiscon_scope_with_only_kvk_attribute(self):
        plugin_options: YiviOptions = {
            "authentication_options": [YiviAuthenticationAttributes.kvk],
            "additional_attributes_groups": [],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W1tbInRlc3QuYXR0cmlidXRlLmt2ayJdXV0=",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(condiscon, [[["test.attribute.kvk"]]])

    @mock_yivi_config()
    def test_create_condiscon_scope_with_only_pseudo_attribute(self):
        plugin_options: YiviOptions = {
            "authentication_options": [YiviAuthenticationAttributes.pseudo],
            "additional_attributes_groups": [],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W1tbXV1d",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(condiscon, [[[]]])

    @mock_yivi_config()
    def test_create_condiscon_scope_without_authentication_options(self):
        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": [],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W10=",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(condiscon, [])

    @mock_yivi_config(
        bsn_claim=["test.attribute.bsn"], legal_subject_claim=["test.attribute.kvk"]
    )
    def test_create_condiscon_scope_with_multiple_authentication_options(self):
        plugin_options: YiviOptions = {
            "authentication_options": [
                YiviAuthenticationAttributes.bsn,
                YiviAuthenticationAttributes.kvk,
                YiviAuthenticationAttributes.pseudo,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W1tbInRlc3QuYXR0cmlidXRlLmJzbiJdLCBbInRlc3QuYXR0cmlidXRlLmt2ayJdLCBbXV1d",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(
            condiscon,
            [
                [
                    ["test.attribute.bsn"],
                    ["test.attribute.kvk"],
                    [],
                ]
            ],
        )

    @mock_yivi_config(bsn_claim=["test.attribute.bsn"])
    def test_create_condiscon_scope_with_additional_attributes(self):
        AttributeGroupFactory(name="first attributes", attributes=["foo", "bar", "baz"])
        AttributeGroupFactory(name="second attributes", attributes=["alice", "bob"])

        plugin_options: YiviOptions = {
            "authentication_options": [YiviAuthenticationAttributes.bsn],
            "additional_attributes_groups": ["first attributes", "second attributes"],
            "bsn_loa": None,
            "kvk_loa": None,
        }
        condiscon_scope = OIDCAuthenticationInitView._yivi_condiscon_scope(
            plugin_options
        )

        self.assertEqual(
            condiscon_scope,
            "signicat:param:condiscon_base64:W1tbInRlc3QuYXR0cmlidXRlLmJzbiJdXSwgW1siZm9vIiwgImJhciIsICJiYXoiXV0sIFtbImFsaWNlIiwgImJvYiJdXV0=",
        )

        # The last part of the condiscon_scope is the actual base64 encoded
        # authentication request content
        base64_part = condiscon_scope.split(":")[-1]

        # Decode to a condiscon array
        decoded_bytes = base64.b64decode(base64_part)
        decoded_str = decoded_bytes.decode("utf-8")
        condiscon = json.loads(decoded_str)

        self.assertEqual(
            condiscon,
            [
                [
                    ["test.attribute.bsn"],
                ],
                [
                    ["foo", "bar", "baz"],
                ],
                [
                    ["alice", "bob"],
                ],
            ],
        )


class YiviGetExtraParamsTest(TestCase):
    """
    Test the get_extra_params method of OIDCAuthenticationInitView.
    """

    @mock_yivi_config(bsn_claim=["test.attribute.bsn"])
    def test_get_extra_params(self):
        AttributeGroupFactory(name="first attributes", attributes=["foo", "bar", "baz"])
        AttributeGroupFactory(name="second attributes", attributes=["alice", "bob"])

        plugin_options: YiviOptions = {
            "authentication_options": [YiviAuthenticationAttributes.bsn],
            "additional_attributes_groups": ["first attributes", "second attributes"],
            "bsn_loa": None,
            "kvk_loa": None,
        }

        extra_params = OIDCAuthenticationInitView(
            options=plugin_options, config_class=YiviOpenIDConnectConfig
        ).get_extra_params(HttpRequest())

        self.assertEqual(
            extra_params,
            {
                "scope": "openid signicat:param:condiscon_base64:W1tbInRlc3QuYXR0cmlidXRlLmJzbiJdXSwgW1siZm9vIiwgImJhciIsICJiYXoiXV0sIFtbImFsaWNlIiwgImJvYiJdXV0="
            },
        )
