from django.test import TestCase

from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory

from ..plugin import YiviPrefill


@temp_private_root()
class YiviPrefillTests(TestCase):
    def test_get_prefill_values(self):
        plugin = YiviPrefill(identifier="yivi")

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="yivi_oidc",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma-demo_gemeente_personalData_firstname": "Joe",
            },
        )
        values = plugin.get_prefill_values(
            submission,
            [
                "value",
                "additional_claims.irma-demo_gemeente_personalData_firstname",
            ],
        )
        expected = {
            "value": "111222333",
            "additional_claims.irma-demo_gemeente_personalData_firstname": "Joe",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_with_unknown_attribute(self):
        plugin = YiviPrefill(identifier="yivi")

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="yivi_oidc",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma-demo_gemeente_personalData_firstname": "Joe",
            },
        )

        values = plugin.get_prefill_values(
            submission,
            [
                "value",
                "additional_claims.irma-demo_gemeente_personalData_firstname",
                "additional_claims.irma-demo_gemeente_personalData_over18",
            ],
        )

        # Expect the unknown attribute not to be resolved
        expected = {
            "value": "111222333",
            "additional_claims.irma-demo_gemeente_personalData_firstname": "Joe",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated(self):
        plugin = YiviPrefill(identifier="yivi")

        submission = SubmissionFactory.create()
        values = plugin.get_prefill_values(
            submission,
            [
                "value",
                "additional_claims.irma-demo_gemeente_personalData_firstname",
            ],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_prefill_values_authenticated_with_wrong_auth_plugin(self):
        plugin = YiviPrefill(identifier="yivi")

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="digid_oidc",
            auth_info__attribute=AuthAttribute.bsn,
        )
        values = plugin.get_prefill_values(
            submission,
            [
                "value",
            ],
        )
        expected = {}
        self.assertEqual(values, expected)
