from django.test import SimpleTestCase, TestCase, override_settings

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as AUTH_PLUGIN_ID,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.submissions.tests.factories import SubmissionFactory

from ....exceptions import PrefillSkipped
from ..plugin import YiviPrefill


class ConfigurationTests(SimpleTestCase):
    maxDiff = None

    @override_settings(LANGUAGE_CODE="en")
    def test_configuration_context(self):
        configuration_context = YiviPrefill.configuration_context()

        expected = {
            "fixed_attributes": [
                {
                    "attribute": "_internal.auth_info.value",
                    "label": "Identifier value",
                    "auth_attribute": "",
                },
                {
                    "attribute": "_internal.bsn",
                    "label": "BSN",
                    "auth_attribute": "bsn",
                },
                {
                    "attribute": "_internal.kvk",
                    "label": "KvK number",
                    "auth_attribute": "kvk",
                },
                {
                    "attribute": "_internal.pseudo",
                    "label": "Pseudo ID",
                    "auth_attribute": "pseudo",
                },
            ],
        }
        self.assertEqual(configuration_context, expected)

    def test_no_static_attributes_available(self):
        attributes = YiviPrefill.get_available_attributes()

        self.assertEqual(attributes, ())


class YiviPluginTests(TestCase):
    maxDiff = None

    def test_populate_fixed_attribute_identifier(self):
        plugin = YiviPrefill("yivi")

        for auth_attr in (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo):
            with self.subTest(auth_info__attribute=auth_attr):
                submission = SubmissionFactory.create(
                    auth_info__value="anything",
                    auth_info__plugin=AUTH_PLUGIN_ID,
                    auth_info__attribute=auth_attr,
                )

                values = plugin.get_prefill_values(
                    submission, attributes=["_internal.auth_info.value"]
                )

                self.assertEqual(
                    values,
                    {"_internal.auth_info.value": "anything"},
                )

    def test_populate_fixed_bsn_attribute(self):
        plugin = YiviPrefill("yivi")

        with self.subTest("with matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.bsn,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.bsn}"]
            )

            self.assertEqual(values, {"_internal.bsn": "anything"})

        with self.subTest("without matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.pseudo,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.bsn}"]
            )

            self.assertEqual(values, {})

    def test_populate_fixed_kvk_attribute(self):
        plugin = YiviPrefill("yivi")

        with self.subTest("with matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.kvk,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.kvk}"]
            )

            self.assertEqual(values, {"_internal.kvk": "anything"})

        with self.subTest("without matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.pseudo,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.kvk}"]
            )

            self.assertEqual(values, {})

    def test_populate_fixed_pseudo_attribute(self):
        plugin = YiviPrefill("yivi")

        with self.subTest("with matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.pseudo,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.pseudo}"]
            )

            self.assertEqual(values, {"_internal.pseudo": "anything"})

        with self.subTest("without matching auth attribute provided"):
            submission = SubmissionFactory.create(
                auth_info__value="anything",
                auth_info__plugin=AUTH_PLUGIN_ID,
                auth_info__attribute=AuthAttribute.bsn,
            )

            values = plugin.get_prefill_values(
                submission, attributes=[f"_internal.{AuthAttribute.pseudo}"]
            )

            self.assertEqual(values, {})

    def test_arbitrary_attributes_taken_from_additional_claims(self):
        plugin = YiviPrefill("yivi")

        submission = SubmissionFactory.create(
            auth_info__value="anything",
            auth_info__plugin=AUTH_PLUGIN_ID,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma": {"gemeente": {"personalData": {"firstName": "Bob"}}}
            },
        )

        values = plugin.get_prefill_values(
            submission,
            attributes=[
                f"_internal.{AuthAttribute.bsn}",
                "irma.gemeente.personalData.firstName",
                "irma.gemeente.personalData.__missing__",
            ],
        )

        self.assertEqual(
            values,
            {
                "_internal.bsn": "anything",
                "irma.gemeente.personalData.firstName": "Bob",
            },
        )

    def test_only_support_main_identifier_role(self):
        """
        Yivi authentication/prefill does not support mandates.
        """
        plugin = YiviPrefill("yivi")

        submission = SubmissionFactory.create(
            auth_info__value="anything",
            auth_info__plugin=AUTH_PLUGIN_ID,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma": {"gemeente": {"personalData": {"firstName": "Bob"}}}
            },
        )

        with self.assertRaises(PrefillSkipped):
            plugin.get_prefill_values(
                submission,
                attributes=[
                    f"_internal.{AuthAttribute.bsn}",
                    "irma.gemeente.personalData.firstName",
                    "irma.gemeente.personalData.__missing__",
                ],
                identifier_role=IdentifierRoles.authorizee,
            )
