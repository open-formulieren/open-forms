from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.constants import FieldChoices
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ..plugin import StufBgPrefill
from .utils import mock_stufbg_client


class StufBgPrefillTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.stuf_bg_service = StufServiceFactory.create()

    def setUp(self) -> None:
        super().setUp()

        self.plugin = StufBgPrefill("test-plugin")
        self.submission = SubmissionFactory.create(bsn="999992314")

        # mock out django-solo interface (we don't have to deal with caches then)
        stufbg_config_patcher = patch(
            "openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo",
            return_value=StufBGConfig(service=self.stuf_bg_service),
        )
        stufbg_config_patcher.start()
        self.addCleanup(stufbg_config_patcher.stop)

    def test_get_available_attributes_returns_correct_attributes(self):
        client_patcher = mock_stufbg_client("StufBgResponse.xml")
        self.addCleanup(client_patcher.stop)
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

    def test_response_external_municipality_returns_correct_attributes(self):
        client_patcher = mock_stufbg_client("StufBgResponseGemeenteVanInschrijving.xml")
        self.addCleanup(client_patcher.stop)
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
        self.assertEqual(values["gemeenteVanInschrijving"], "Amsterdam")

    def test_get_available_attributes_when_some_attributes_are_not_returned(self):
        client_patcher = mock_stufbg_client("StufBgResponseMissingSomeData.xml")
        self.addCleanup(client_patcher.stop)
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

    def test_voorvoegsel_is_parsed(self):
        client_patcher = mock_stufbg_client("StufBgResponseWithVoorvoegsel.xml")
        self.addCleanup(client_patcher.stop)
        attributes = FieldChoices.attributes.keys()

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
        client_patcher = mock_stufbg_client("StufBgErrorResponse.xml")
        self.addCleanup(client_patcher.stop)

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

    def test_get_available_attributes_when_no_answer_is_returned(self):
        client_patcher = mock_stufbg_client("StufBgNoAnswerResponse.xml")
        self.addCleanup(client_patcher.stop)
        attributes = FieldChoices.attributes.keys()

        with self.assertLogs() as logs:
            values = self.plugin.get_prefill_values(self.submission, attributes)

            self.assertEqual(values, {})
            self.assertEqual(logs.records[0].fault, {})
