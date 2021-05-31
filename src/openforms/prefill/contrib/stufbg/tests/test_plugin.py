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
        client_mock.return_value.get_client.return_value.get_values_for_attributes.return_value = loader.render_to_string(
            "stuf/stuf_bg/tests/responses/StufBgResponse.xml"
        )
        attributes = FieldChoices.attributes.keys()

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEquals(values["bsn"], "999992314")
        self.assertEquals(values["voornamen"], "Media")
        self.assertEquals(values["geslachtsnaam"], "Maykin")
        self.assertEquals(values["straatnaam"], "Keizersgracht")
        self.assertEquals(values["huisnummer"], "117")
        self.assertEquals(values["huisletter"], "A")
        self.assertEquals(values["huisnummertoevoeging"], "B")
        self.assertEquals(values["postcode"], "1015 CJ")
        self.assertEquals(values["woonplaatsNaam"], "Amsterdam")
