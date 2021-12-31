import uuid
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.template import loader
from django.test import TestCase
from django.utils import timezone

import requests_mock
import xmltodict
from freezegun import freeze_time
from glom import glom
from lxml import etree

from openforms.logging.models import TimelineLogProxy
from openforms.prefill.contrib.stufbg.plugin import ATTRIBUTES_TO_STUF_BG_MAPPING
from stuf.constants import SOAP_VERSION_CONTENT_TYPES, SOAPVersion
from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS, FieldChoices
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_zds.client import nsmap
from stuf.tests.factories import StufServiceFactory


class StufBGConfigTests(TestCase):
    def setUp(self):
        super().setUp()
        self.service = StufServiceFactory.create()
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
        self.assertEqual(
            m.last_request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/bg/0310/npsLv01",
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

    def test_all_attributes_are_mapped(self):
        available_attributes = FieldChoices.attributes.keys()
        for attribute in available_attributes:
            with self.subTest(attribute=attribute):
                glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                if not glom_target:
                    self.fail(f"unmapped attribute: {attribute}")

    def test_getting_request_data_returns_valid_data(self):
        available_attributes = FieldChoices.attributes.keys()
        test_bsn = "999992314"

        with open(
            f"{settings.BASE_DIR}/src/stuf/stuf_bg/xsd/bg0310/vraagAntwoord/bg0310_namespace.xsd",
            "r",
        ) as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)

            data = self.client.get_request_data(test_bsn, available_attributes)
            doc = etree.parse(BytesIO(bytes(data, encoding="UTF-8")))
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
                    f'Attributes "{available_attributes}" produces an invalid StUF-BG. '
                    f"Error: {xmlschema.error_log.last_error.message}"
                )

            # convert to dict to glom
            bg_obj = doc.getroot().xpath("//bg:object", namespaces=nsmap)
            data_dict = xmltodict.parse(
                etree.tostring(bg_obj[0]),
                process_namespaces=True,
                namespaces=NAMESPACE_REPLACEMENTS,
            )["object"]
            sentinel = object()

            # now test if all attributes appear as nodes in the request data
            # TODO this is in-accurate as we don't check the actual nodes (nil/no-value etc)
            for attribute in available_attributes:
                with self.subTest(attribute=attribute):
                    glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                    if not glom_target:
                        self.fail(f"unmapped attribute: {attribute}")
                    else:
                        value = glom(data_dict, glom_target, default=sentinel)
                        if value == sentinel:
                            self.fail(
                                f"missing attribute in request {attribute} (as {glom_target}"
                            )
