import requests_mock

from unittest.mock import patch

from django.template import loader
from django.test import TestCase


from get_address.stuf_bg.models import StufBGConfig
from openforms.registrations.contrib.stuf_zds.tests.factories import SoapServiceFactory


class StufBGConfigTests(TestCase):

    def setUp(self):
        super().setUp()
        self.service = SoapServiceFactory.create()
        self.client = StufBGConfig.get_solo()
        self.client.service = self.service
        self.client.save()

    @patch("django.utils.dateformat.format")
    @patch("uuid.uuid4")
    def test_get_address(self, uuid_mock, dateformat_mock):
        test_bsn = 123456789
        test_uuid = "00000000-0000-0000-0000-000000000000"
        test_dateformat = "20200919094000"
        uuid_mock.return_value = test_uuid
        dateformat_mock.return_value = test_dateformat

        with requests_mock.Mocker() as m:
            m.post(
                self.service.url,
                content=bytes(
                    loader.render_to_string(
                        # "response/ResponseOneOuder.xml",
                        "get_address/stuf_bg/tests/responses/ResponseAddress.xml",
                        context={
                            "referentienummer": test_uuid,
                            "tijdstip_bericht": test_dateformat,
                            "zender_organisatie": self.service.ontvanger_organisatie,
                            "zender_applicatie": self.service.ontvanger_applicatie,
                            "zender_administratie": self.service.ontvanger_administratie,
                            "zender_gebruiker": self.service.ontvanger_gebruiker,
                            "ontvanger_organisatie": self.service.zender_organisatie,
                            "ontvanger_applicatie": self.service.zender_applicatie,
                            "ontvanger_administratie": self.service.zender_administratie,
                            "ontvanger_gebruiker": self.service.zender_gebruiker,
                        },
                    ),
                    encoding="utf-8",
                ),
            )
            address = self.client.get_address(test_bsn)
            self.assertTrue(m.called)

        self.assertEqual(address['street_name'], 'Keizersgracht')
        self.assertEqual(address['house_number'], '117')
        self.assertEqual(address['house_letter'], 'A')
        self.assertEqual(address['house_letter_addition'], 'B')
        self.assertEqual(address['postcode'], '1015 CJ')
        self.assertEqual(address['city'], 'Amsterdam')
