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

from openforms.logging.models import TimelineLogProxy
from stuf.constants import SOAP_VERSION_CONTENT_TYPES, SOAPVersion
from stuf.tests.factories import StufServiceFactory

from ..constants import FieldChoices
from ..models import StufBGConfig


class StufBGConfigTests(TestCase):
    def setUp(self):
        super().setUp()
        self.service = StufServiceFactory.create()
        self.config = StufBGConfig.get_solo()
        self.config.service = self.service.soap_service
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
                self.service.soap_service.url,
                content=bytes(
                    loader.render_to_string(
                        "stuf_bg/tests/responses/StufBgResponse.xml",
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
            self.client.get_values_for_attributes(
                "999992314", list(FieldChoices.values.keys())
            )

        self.assertEqual(m.last_request.method, "POST")
        self.assertEqual(
            m.last_request.headers["Content-Type"],
            SOAP_VERSION_CONTENT_TYPES.get(SOAPVersion.soap12),
        )

        with open(
            f"{settings.BASE_DIR}/src/stuf/stuf_bg/xsd/bg0310/vraagAntwoord/bg0310_namespace.xsd",
            "r",
        ) as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)

            doc = etree.parse(BytesIO(bytes(m.last_request.body, encoding="UTF-8")))
            el = (
                doc.getroot()
                .xpath(
                    "soap:Body",
                    namespaces={"soap": "http://schemas.xmlsoap.org/soap/envelope/"},
                )[0]
                .getchildren()[0]
            )
            if not xmlschema.validate(el):
                self.fail(
                    f'Request body "{m.last_request.body}" is not valid against StUF-BG XSDs. '
                    f"Error: {xmlschema.error_log.last_error.message}"
                )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_bg_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_bg_request.txt"
            ).count(),
            1,
        )

    def test_getting_request_data_returns_valid_data(self):
        available_attributes = FieldChoices.attributes.keys()
        test_bsn = "999992314"

        subsets = []

        # This gets all possible subsets that can be requested and tests them
        # Since the order of attributes matter it is important all possible combinations
        #   are tested to ensure certain combinations aren't invalid
        for L in range(1, len(available_attributes) + 1):
            for subset in itertools.combinations(available_attributes, L):
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
                            f'Attributes "{subset}" produces an invalid StUF-BG. '
                            f"Error: {xmlschema.error_log.last_error.message}"
                        )
                    for attribute in subset:
                        with self.subTest(subset=subset, attribute=attribute):
                            self.assertIn(attribute, data)
