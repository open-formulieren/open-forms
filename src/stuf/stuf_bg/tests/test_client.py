from functools import lru_cache
from pathlib import Path
from random import shuffle
from unittest.mock import patch

from django.conf import settings
from django.template import loader
from django.test import SimpleTestCase, tag
from django.utils import timezone

import requests_mock
import xmltodict
from glom import T as GlomTarget, glom
from lxml import etree

from openforms.logging.tests.utils import disable_timelinelog
from openforms.prefill.contrib.stufbg.plugin import ATTRIBUTES_TO_STUF_BG_MAPPING
from soap.constants import SOAP_VERSION_CONTENT_TYPES, SOAPVersion
from stuf.models import StufService
from stuf.stuf_zds.client import nsmap
from stuf.tests.factories import StufServiceFactory
from stuf.xml import fromstring

from ..client import NoServiceConfigured, StufBGClient, get_client
from ..constants import NAMESPACE_REPLACEMENTS, FieldChoices
from ..models import StufBGConfig

PATH_XSDS = (Path(settings.BASE_DIR) / "src" / "stuf" / "stuf_bg" / "xsd").resolve()
STUF_BG_XSD = PATH_XSDS / "bg0310" / "vraagAntwoord" / "bg0310_namespace.xsd"


@lru_cache
def _stuf_bg_xmlschema_doc():
    # don't add the etree.XMLSchema construction to this; it's an object
    # that contains state like error_log

    with STUF_BG_XSD.open("r") as infile:
        return etree.parse(infile)


def _extract_soap_body(full_doc: str | bytes):
    doc = fromstring(full_doc)
    soap_body = doc.xpath(
        "soap:Body",
        namespaces={"soap": "http://schemas.xmlsoap.org/soap/envelope/"},
    )[0].getchildren()[0]
    return soap_body


def _stuf_bg_response(service: StufService):
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


class StufBGConfigTests(SimpleTestCase):
    @patch(
        "stuf.stuf_bg.client.StufBGConfig.get_solo",
        return_value=StufBGConfig(service=None),
    )
    def test_client_requires_a_service(self, m_get_solo):
        with self.assertRaises(NoServiceConfigured):
            get_client()

    def test_all_prefill_attributes_are_mapped(self):
        for attribute in FieldChoices:
            with self.subTest(attribute=attribute):
                glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                self.assertTrue(glom_target, f"unmapped attribute: {attribute}")


@disable_timelinelog()
class StufBGClientTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.stuf_service = StufServiceFactory.build(soap_service__soap_version="1.1")
        self.stufbg_client = StufBGClient(service=self.stuf_service)

    def test_order_of_attributes_in_template_is_correct(self):
        # Any attribute we expect to request MUST be listed here
        all_available_attributes = ["inp.heeftAlsKinderen"] + FieldChoices.values

        # order in function call doesn't matter
        shuffle(all_available_attributes)

        test_bsn = "999992314"
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(self.stuf_service.soap_service.url, status_code=200)
            self.stufbg_client.get_values_for_attributes(
                test_bsn, all_available_attributes
            )

        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)

        # validate soap message with xsd
        # order of all elements in request doc does matter!
        xmlschema.assert_(soap_body)

    def test_soap_request_method_and_headers(self):
        test_bsn = "999992314"
        with requests_mock.Mocker() as m:
            m.post(self.stuf_service.soap_service.url)
            # perform request
            self.stufbg_client.get_values_for_attributes(test_bsn, FieldChoices.values)

        self.assertEqual(m.last_request.method, "POST")
        self.assertEqual(
            m.last_request.headers["Content-Type"],
            SOAP_VERSION_CONTENT_TYPES.get(SOAPVersion.soap11),
        )
        self.assertEqual(
            m.last_request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/bg/0310/npsLv01",
        )

    def test_getting_request_data_returns_valid_data(self):
        available_attributes = FieldChoices.values
        test_bsn = "999992314"

        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_service.soap_service.url,
                status_code=200,
                content=_stuf_bg_response(self.stuf_service),
            )
            response_dict = self.stufbg_client.get_values(
                test_bsn, available_attributes
            )

        self.assertFalse(_contains_nils(response_dict))

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
        for attribute in FieldChoices:
            if attribute == "voorvoegselGeslachtsnaam":
                continue  # That's a nil.
            with self.subTest(attribute=attribute):
                glom_target = ATTRIBUTES_TO_STUF_BG_MAPPING.get(attribute)
                in_request = glom(request_dict, glom_target, default=missing)
                self.assertTrue(
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
                self.assertTrue(
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
            m.post(self.stuf_service.soap_service.url, content=b"I am not valid XML")

            with self.assertRaises(Exception):
                self.stufbg_client.get_values(
                    "999992314", list(FieldChoices.values.keys())
                )

    def test_inp_heeftAlsKinderen(self):
        test_bsn = "999992314"

        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())

        with requests_mock.Mocker() as m:
            m.post(self.stuf_service.soap_service.url, status_code=200)
            self.stufbg_client.get_values_for_attributes(
                test_bsn, ["inp.heeftAlsKinderen"]
            )

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

    @tag("gh-4338")
    @requests_mock.Mocker()
    def test_scattered_namespaces(self, m):
        XML = b"""<?xml version='1.0' encoding='UTF-8'?>
        <soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope">
            <soapenv:Header />
            <soapenv:Body>
                <BG:npsLa01 xmlns:BG="http://www.egem.nl/StUF/sector/bg/0310"
                    xmlns:StUF="http://www.egem.nl/StUF/StUF0301"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <BG:stuurgegevens>
                        <StUF:berichtcode>La01</StUF:berichtcode>
                        <StUF:zender>

                            <StUF:applicatie>CGS</StUF:applicatie>


                        </StUF:zender>
                        <StUF:ontvanger>
                            <StUF:organisatie>Maykin</StUF:organisatie>
                            <StUF:applicatie>OpenForms</StUF:applicatie>


                        </StUF:ontvanger>
                        <StUF:referentienummer>S17170448031</StUF:referentienummer>
                        <StUF:tijdstipBericht>2024053011095409</StUF:tijdstipBericht>
                        <StUF:crossRefnummer>6551d7e5-515c-4c30-b249-e8aab590ac06</StUF:crossRefnummer>
                        <StUF:entiteittype>NPS</StUF:entiteittype>
                    </BG:stuurgegevens>
                    <BG:parameters>
                        <StUF:indicatorVervolgvraag>false</StUF:indicatorVervolgvraag>
                    </BG:parameters>
                    <BG:antwoord>
                        <BG:object StUF:entiteittype="NPS">
                            <BG:inp.bsn>111222333</BG:inp.bsn>
                            <BG:geslachtsnaam>Janssen</BG:geslachtsnaam>
                            <BG:voorvoegselGeslachtsnaam xsi:nil="true" StUF:noValue="geenWaarde" />
                            <BG:geboortedatum>19820304</BG:geboortedatum>
                        </BG:object>
                    </BG:antwoord>
                </BG:npsLa01>
            </soapenv:Body>
        </soapenv:Envelope>
        """
        m.post(self.stuf_service.soap_service.url, content=XML)

        response_data = self.stufbg_client.get_values("999992314", ["irrelevant"])

        expected = {
            "inp.bsn": "111222333",
            "geslachtsnaam": "Janssen",
            "voorvoegselGeslachtsnaam": None,
            "geboortedatum": "19820304",
        }
        for key, value in expected.items():
            with self.subTest(key=key, value=value):
                self.assertEqual(response_data.get(key), value)


def _contains_nils(d: dict):
    """Check if xmltodict result contains xsi:nil="true" or StUF:noValue="geenWaarde"
    where
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    StUF = "http://www.egem.nl/StUF/StUF0301"
    """

    for k, v in d.items():
        if (k == "@http://www.w3.org/2001/XMLSchema-instance:nil" and v == "true") or (
            k == "@noValue" and v == "geenWaarde"
        ):
            return True
        if isinstance(v, dict) and _contains_nils(v):
            return True
