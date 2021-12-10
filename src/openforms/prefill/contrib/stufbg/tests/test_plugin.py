from unittest.mock import patch

from django.template import loader
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.constants import FieldChoices
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ..plugin import StufBgPrefill


class StufBgPrefillTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        stuf_bg_service = StufServiceFactory.create()
        config = StufBGConfig.get_solo()
        config.service = stuf_bg_service
        config.save()

    def setUp(self) -> None:
        super().setUp()

        self.plugin = StufBgPrefill("test-plugin")
        self.submission = SubmissionFactory.create(bsn="999992314")

    def test_get_available_attributes_returns_correct_attributes(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
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

    def test_response_external_municipality_returns_correct_attributes(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponseGemeenteVanInschrijving.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
            values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["gemeenteVanInschrijving"], "Amsterdam")

    def test_get_available_attributes_when_some_attributes_are_not_returned(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponseMissingSomeData.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
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

    def test_voorvoegsel_is_parsed(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponseWithVoorvoegsel.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
            values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["voorvoegselGeslachtsnaam"], "van")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")

    def test_get_available_attributes_when_error_occurs(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgErrorResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
            with self.assertLogs() as logs:
                values = self.plugin.get_prefill_values(self.submission, attributes)

                self.assertEqual(values, {})
                self.assertEqual(logs.records[0].fault["faultcode"], "soapenv:Server")
                self.assertEqual(
                    logs.records[0].fault["faultstring"], "Policy Falsified"
                )
                self.assertEqual(
                    logs.records[0].fault["detail"][
                        "http://www.layer7tech.com/ws/policy/fault:policyResult"
                    ]["@status"],
                    "Error in Assertion Processing",
                )

    def test_get_available_attributes_when_no_answer_is_returned(self):
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgNoAnswerResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
            with self.assertLogs() as logs:
                values = self.plugin.get_prefill_values(self.submission, attributes)

                self.assertEqual(values, {})
                self.assertEqual(logs.records[0].fault, {})
