from unittest.mock import patch

from django.template import loader
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.constants import FieldChoices

from ..plugin import StufBgPrefill


class StufBgPrefillTests(TestCase):
    def setUp(self) -> None:
        self.plugin = StufBgPrefill("test-plugin")
        self.submission = SubmissionFactory.create(bsn="999992314")

    @patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    def test_get_available_attributes_returns_correct_attributes(self, client_mock):
        get_values_for_attributes_mock = (
            client_mock.return_value.get_client.return_value.get_values_for_attributes
        )
        get_values_for_attributes_mock.return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")

    @patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    def test_get_available_attributes_when_some_attributes_are_not_returned(
        self, client_mock
    ):
        get_values_for_attributes_mock = (
            client_mock.return_value.get_client.return_value.get_values_for_attributes
        )
        get_values_for_attributes_mock.return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponseMissingSomeData.xml"
        )
        attributes = FieldChoices.attributes.keys()

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")
        self.assertNotIn("huisnummertoevoeging", values)
        self.assertNotIn("huisletter", values)

    @patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    def test_get_available_attributes_when_error_occurs(self, client_mock):
        get_values_for_attributes_mock = (
            client_mock.return_value.get_client.return_value.get_values_for_attributes
        )
        get_values_for_attributes_mock.return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgErrorResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with self.assertLogs() as logs:
            values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values, {})
        self.assertEqual(logs.records[0].fault["faultcode"], "soapenv:Server")
        self.assertEqual(logs.records[0].fault["faultstring"], "Policy Falsified")
        self.assertEqual(
            logs.records[0].fault["detail"][
                "http://www.layer7tech.com/ws/policy/fault:policyResult"
            ]["@status"],
            "Error in Assertion Processing",
        )

    @patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    def test_get_available_attributes_when_no_answer_is_returned(self, client_mock):
        get_values_for_attributes_mock = (
            client_mock.return_value.get_client.return_value.get_values_for_attributes
        )
        get_values_for_attributes_mock.return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponseNoAnswer.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with self.assertLogs() as logs:
            values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values, {})
        self.assertEqual(logs.records[0].fault, {})
