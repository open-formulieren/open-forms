from functools import lru_cache
from pathlib import Path
from random import shuffle

from django.conf import settings
from django.template import loader
from django.test import TestCase, tag
from django.utils import timezone

import requests_mock
import xmltodict
from glom import T as GlomTarget, glom
from lxml import etree

from openforms.logging.models import TimelineLogProxy
from openforms.prefill.contrib.stufbg.plugin import ATTRIBUTES_TO_STUF_BG_MAPPING
from soap.constants import SOAP_VERSION_CONTENT_TYPES, SOAPVersion
from stuf.stuf_bg.client import StufBGClient
from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS, FieldChoices
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_zds.client import nsmap
from stuf.tests.factories import StufServiceFactory
from stuf.xml import fromstring

PATH_XSDS = (Path(settings.BASE_DIR) / "src" / "stuf" / "stuf_bg" / "xsd").resolve()
STUF_BG_XSD = PATH_XSDS / "bg0310" / "vraagAntwoord" / "bg0310_namespace.xsd"


@lru_cache
def _stuf_bg_xmlschema_doc():
    # don't add the etree.XMLSchema construction to this; it's an object
    # that contains state like error_log

    with STUF_BG_XSD.open("r") as infile:
        return etree.parse(infile)


def _extract_soap_body(full_doc: str):
    doc = fromstring(full_doc)
    soap_body = doc.xpath(
        "soap:Body",
        namespaces={"soap": "http://schemas.xmlsoap.org/soap/envelope/"},
    )[0].getchildren()[0]
    return soap_body


def _stuf_bg_response(service):
    response_body = bytes(
        loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponse.xml",
            context={
                "referentienummer": "38151851-0fe9-4463-ba39-416042b8f406",
                "tijdstip_bericht": timezone.now().strftime("%Y%m%d%H%M%S"),
                "zender_organisatie": service.ontvanger_organisatie,
                "zender_applicatie": service.ontvanger_applicatie,
                "zender_administratie": service.ontvanger_administratie,
                "zender_gebruiker": service.ontvanger_gebruiker,
                "ontvanger_organisatie": service.zender_organisatie,
                "ontvanger_applicatie": service.zender_applicatie,
                "ontvanger_administratie": service.zender_administratie,
                "ontvanger_gebruiker": service.zender_gebruiker,
            },
        ),
        encoding="utf-8",
    )
    # assert this mocked response is valid
    xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
    xmlschema.assert_(_extract_soap_body(response_body))
    return response_body


class StufBGConfigTests(TestCase):
    def test_client_requires_a_service(self):
        config = StufBGConfig(service=None)

        with self.assertRaises(RuntimeError):
            config.get_client()

    def test_all_prefill_attributes_are_mapped(self):
        available_attributes = FieldChoices.values
        for attribute in available_attributes:
            with self.subTest(attribute=attribute):
                glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                self.assert_(glom_target, f"unmapped attribute: {attribute}")


class StufBGClientTests(TestCase):
    def setUp(self):
        self.client = StufBGClient(
            service=StufServiceFactory.build(soap_service__soap_version="1.1")
        )

    def test_order_of_attributes_in_template_is_correct(self):
        # Any attribute we expect to request MUST be listed here
        all_available_attributes = ["inp.heeftAlsKinderen"] + FieldChoices.values

        # order in function call doesn't matter
        shuffle(all_available_attributes)

        test_bsn = "999992314"
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(self.client.service.soap_service.url, status_code=200)
            self.client.get_values_for_attributes(test_bsn, all_available_attributes)

        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)

        # validate soap message with xsd
        # order of all elements in request doc does matter!
        xmlschema.assert_(soap_body)

    def test_soap_request_method_and_headers(self):
        test_bsn = "999992314"
        with requests_mock.Mocker() as m:
            m.post(self.client.service.soap_service.url)
            # perform request
            self.client.get_values_for_attributes(test_bsn, FieldChoices.values)

        self.assertEqual(m.last_request.method, "POST")
        self.assertEqual(
            m.last_request.headers["Content-Type"],
            SOAP_VERSION_CONTENT_TYPES.get(SOAPVersion.soap11),
        )
        self.assertEqual(
            m.last_request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/bg/0310/npsLv01",
        )

    def test_soap_request_gets_logged(self):
        test_bsn = "999992314"

        with requests_mock.Mocker() as m:
            m.post(self.client.service.soap_service.url)
            # perform request
            self.client.get_values_for_attributes(test_bsn, FieldChoices.values)

        logged_events = TimelineLogProxy.objects.filter_event("stuf_bg_request")
        self.assertTrue(logged_events.exists(), "StUF-BG request wasn't logged.")

    def test_getting_request_data_returns_valid_data(self):
        available_attributes = FieldChoices.values
        test_bsn = "999992314"

        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(
                self.client.service.soap_service.url,
                status_code=200,
                content=_stuf_bg_response(self.client.service),
            )
            response_dict = self.client.get_values(test_bsn, available_attributes)

        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)

        # validate request
        xmlschema.assert_(soap_body)

        # convert to dict to glom
        bg_obj = soap_body.xpath("//bg:object", namespaces=nsmap)
        request_dict = xmltodict.parse(
            etree.tostring(bg_obj[0]),
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )["object"]
        missing = object()

        # now test if all attributes appear as nodes in the request data
        # TODO this is in-accurate as we don't check the actual nodes (nil/no-value etc)
        for attribute in available_attributes:
            with self.subTest(attribute=attribute):
                glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                in_request = glom(request_dict, glom_target, default=missing)
                self.assert_(
                    in_request is not missing,
                    f"missing attribute in request {attribute} (as {glom_target})",
                )

                attributes_not_in_mock_response = [
                    FieldChoices.geboorteplaats,
                    FieldChoices.landAdresBuitenland,
                    FieldChoices.adresBuitenland1,
                    FieldChoices.adresBuitenland2,
                    FieldChoices.adresBuitenland3,
                ]
                if attribute in attributes_not_in_mock_response:
                    continue
                in_response = glom(response_dict, glom_target, default=missing)
                self.assert_(
                    in_response is not missing,
                    f"missing attribute in response {attribute} (as {glom_target})",
                )

    @tag("gh-1842")
    def test_errors_are_not_swallowed(self):
        """
        Assert that client exceptions are propagated to the caller.

        Regression test for #1842 - in this issue the exceptions were logged to Sentry,
        but not visible in the submission (prefill) logs (neither success nor error).
        The client may not swallow exceptions, but must re-raise them so that the
        generic prefill error handler can properly dispatch the logevents (see
        :func:`openforms.prefill._fetch_prefill_values`).
        """
        with requests_mock.Mocker() as m:
            m.post(self.client.service.soap_service.url, content=b"I am not valid XML")

            with self.assertRaises(Exception):
                self.client.get_values("999992314", list(FieldChoices.values.keys()))

    def test_inp_heeftAlsKinderen(self):
        test_bsn = "999992314"

        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(self.client.service.soap_service.url, status_code=200)
            self.client.get_values_for_attributes(test_bsn, ["inp.heeftAlsKinderen"])

        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        # validate soap message with xsd
        xmlschema.assert_(soap_body)

        # convert to dict to glom
        bg_obj = soap_body.xpath("//bg:object", namespaces=nsmap)
        data_dict = xmltodict.parse(
            etree.tostring(bg_obj[0]),
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )["object"]
        missing = object()

        value = glom(data_dict, GlomTarget["inp.heeftAlsKinderen"], default=missing)
        self.assertNotEqual(value, missing)
