import itertools
import uuid
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.template import loader
from django.test import TestCase
from django.utils import timezone

import requests_mock
from freezegun import freeze_time
from lxml import etree

from stuf.stuf_bg.constants import Attributes
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import SoapServiceFactory


class StufBGConfigTests(TestCase):
    def setUp(self):
        super().setUp()
        self.service = SoapServiceFactory.create()
        self.config = StufBGConfig.get_solo()
        self.config.service = self.service
        self.config.save()
        self.client = self.config.get_client()

    @freeze_time("2020-12-11T10:53:19+01:00")
    @patch(
        "stuf.stuf_bg.client.uuid.uuid4",
        return_value=uuid.UUID("38151851-0fe9-4463-ba39-416042b8f406"),
    )
    def test_get_address(self, _mock):
        with requests_mock.Mocker() as m:
            m.post(
                self.service.url,
                content=bytes(
                    loader.render_to_string(
                        "stuf/stuf_bg/tests/responses/StufBgResponse.xml",
                        context={
                            "referentienummer": "38151851-0fe9-4463-ba39-416042b8f406",
                            "tijdstip_bericht": timezone.now(),
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
            response_data = self.client.get_values_for_attributes(
                "999992314", list(Attributes.values.keys())
            )
            # TODO Add additional asserts to better test call
            self.assertEqual(m.last_request.method, "POST")

        self.assertIn("Keizersgracht", str(response_data))
        self.assertIn("117", str(response_data))
        self.assertIn("A", str(response_data))
        self.assertIn("B", str(response_data))
        self.assertIn("1015 CJ", str(response_data))
        self.assertIn("Amsterdam", str(response_data))

    def test_getting_request_data_returns_valid_data(self):
        available_attribute = Attributes.attributes.keys()
        test_bsn = "999992314"

        subsets = []

        # This gets all possible subsets that can be requested and tests them
        # Possibly overkill but this ensure certain combinations won't fail while others pass
        for L in range(1, len(available_attribute) + 1):
            for subset in itertools.combinations(available_attribute, L):
                subsets.append(list(subset))

        with open(
            f"{settings.BASE_DIR}/src/stuf/stuf_bg/xsd/bg0310/vraagAntwoord/bg0310_namespace.xsd",
            "r",
        ) as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)

            for subset in subsets:
                with self.subTest(subset=subset):
                    data = self.client.get_request_data(test_bsn, subset)
                    doc = etree.parse(BytesIO(bytes(data, encoding="UTF-8")))
                    el = (
                        doc.getroot()
                        .xpath(
                            "soap:Body",
                            namespaces={
                                "soap": "http://schemas.xmlsoap.org/soap/envelope/"
                            },
                        )[0]
                        .getchildren()[0]
                    )
                    if not xmlschema.validate(el):
                        self.fail(
                            f'Attributes "{subset}" produces an invalid xml '
                            f"with error {xmlschema.error_log.last_error.message}"
                        )
