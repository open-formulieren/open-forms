import base64
import json
import os
import uuid
from collections import OrderedDict
from datetime import timedelta
from typing import Tuple

from django.core.serializers.json import DjangoJSONEncoder
from django.template import loader
from django.utils import timezone
from django.utils.safestring import mark_safe

import requests
from lxml import etree
from lxml.etree import Element
from requests import Response

from openforms.registrations.contrib.stuf_zds.models import SoapService

nsmap = OrderedDict(
    (
        ("zkn", "http://www.egem.nl/StUF/sector/zkn/0310"),
        ("bg", "http://www.egem.nl/StUF/sector/bg/0310"),
        ("stuf", "http://www.egem.nl/StUF/StUF0301"),
        ("zds", "http://www.stufstandaarden.nl/koppelvlak/zds0120"),
        ("gml", "http://www.opengis.net/gml"),
        ("xsi", "http://www.w3.org/2001/XMLSchema-instance"),
        # ("soap11env", "http://www.w3.org/2003/05/soap-envelope"), # ugly
        ("soapenv", "http://www.w3.org/2003/05/soap-envelope"),  # added
    )
)

SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "vendor", "Zaak_DocumentServices_1_1_02"
)
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
DATETIME_FORMAT = "%Y%m%d%H%M%S"


def fmt_soap_datetime(d):
    return d.strftime(DATETIME_FORMAT)


def fmt_soap_date(d):
    return d.strftime(DATE_FORMAT)


def fmt_soap_time(d):
    return d.strftime(TIME_FORMAT)


def xml_value(xml, xpath, namespaces=nsmap):
    elements = xml.xpath(xpath, namespaces=namespaces)
    if len(elements) == 1:
        return elements[0].text
    else:
        raise ValueError(f"xpath not found {xpath}")


class StufZDSClient:
    def __init__(self, service: SoapService):
        self.service = service

    def _get_headers(self):
        credentials = f"{self.service.user}:{self.service.password}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")
        return {
            "Authorization": "Basic " + encoded_credentials,
            "Content-Type": "application/soap+xml",
        }

    def _get_request_base_context(self, options):
        return {
            "zender_organisatie": self.service.zender_organisatie,
            "zender_applicatie": self.service.zender_applicatie,
            "zender_gebruiker": self.service.zender_gebruiker,
            "zender_administratie": self.service.zender_administratie,
            "ontvanger_organisatie": self.service.ontvanger_organisatie,
            "ontvanger_applicatie": self.service.ontvanger_applicatie,
            "ontvanger_gebruiker": self.service.ontvanger_gebruiker,
            "ontvanger_administratie": self.service.ontvanger_administratie,
            "tijdstip_bericht": fmt_soap_datetime(timezone.now()),
            "gemeentecode": options["gemeentecode"],
            "zds_zaaktype_code": options["zds_zaaktype_code"],
            "zds_zaaktype_omschrijving": options["zds_zaaktype_omschrijving"],
            "zaak_omschrijving": options["omschrijving"],
            "document_omschrijving": options["omschrijving"],
            "referentienummer": options["referentienummer"],
            "tijdstip_registratie": fmt_soap_datetime(timezone.now()),
            "datum_vandaag": fmt_soap_date(timezone.now()),
        }

    def _wrap_soap_envelope(self, xml_str: str) -> str:
        return loader.render_to_string(
            "stuf_zds/soap/includes/envelope.xml", {"content": mark_safe(xml_str)}
        )

    def _load_schema(self, path: str):
        path = os.path.join(SCHEMA_DIR, path)
        with open(path, "r") as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)
        return xmlschema

    def _make_request(
        self,
        template_name: str,
        schema_path: str,
        context: dict,
        sync=False,
    ) -> Tuple[Response, Element]:
        cert = (
            (self.service.certificate.path, self.service.certificate_key.path)
            if self.service.certificate and self.service.certificate_key
            else (None, None)
        )

        request_body = loader.render_to_string(template_name, context)

        # print(request_body)

        # TODO enable schema validation
        # doc = etree.parse(StringIO(request_body))
        # xmlschema = self._load_schema(schema_path)
        # if not xmlschema.validate(doc):
        #     raise ValidationError(xmlschema.error_log.last_error.message)

        request_data = self._wrap_soap_envelope(request_body)

        url = self.service.url
        if sync:
            url = f"{url}{self.service.endpoint_sync}"
        else:
            url = f"{url}{self.service.endpoint_async}"

        response = requests.post(
            url,
            data=request_data,
            headers=self._get_headers(),
            cert=cert,
        )
        # TODO error handling?
        if response.status_code < 200 or response.status_code >= 400:
            print(parse_soap_error_text(response))
            response.raise_for_status()
        return response, etree.fromstring(response.content)

    def create_zaak_identificatie(self, options):
        template = "stuf_zds/soap/genereerZaakIdentificatie.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context(options)
        response, xml = self._make_request(template, schema, context, sync=True)

        zaak_identificatie = xml_value(
            xml, "//zkn:zaak/zkn:identificatie", namespaces=nsmap
        )

        return zaak_identificatie

    def create_zaak(self, options, zaak_identificatie, data):
        template = "stuf_zds/soap/creeerZaak.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context(options)
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
            }
        )
        context.update(data)
        response, xml = self._make_request(template, schema, context)

        return None

    def create_document_identificatie(self, options):
        template = "stuf_zds/soap/genereerDocumentIdentificatie.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context(options)
        response, xml = self._make_request(template, schema, context, sync=True)

        document_identificatie = xml_value(
            xml, "//zkn:document/zkn:identificatie", namespaces=nsmap
        )

        return document_identificatie

    def create_zaak_document(self, options, zaak_id, doc_id, body):
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"

        file_content = base64.b64encode(
            json.dumps(body, cls=DjangoJSONEncoder).encode()
        ).decode()

        context = self._get_request_base_context(options)
        context.update(
            {
                "zaak_identificatie": zaak_id,
                "document_identificatie": doc_id,
                "file_content": file_content,
                "file_name": f"file-{doc_id}.b64.txt",
            }
        )
        response, xml = self._make_request(template, schema, context)

        return None


def parse_soap_error_text(response):
    """
    <?xml version='1.0' encoding='utf-8'?>
    <soap11env:Envelope xmlns:soap11env="http://www.w3.org/2003/05/soap-envelope">
      <soap11env:Body>
        <soap11env:Fault>
          <faultcode>soap11env:client</faultcode>
          <faultstring>Berichtbody is niet conform schema in sectormodel</faultstring>
          <faultactor/>
          <detail>
            <ns0:Fo02Bericht xmlns:ns0="http://www.egem.nl/StUF/StUF0301">
              <ns0:stuurgegevens>
                <ns0:berichtcode>Fo02</ns0:berichtcode>
              </ns0:stuurgegevens>
              <ns0:body>
                <ns0:code>StUF055</ns0:code>
                <ns0:plek>client</ns0:plek>
                <ns0:omschrijving>Berichtbody is niet conform schema in sectormodel</ns0:omschrijving>
                <ns0:details>:52:0:ERROR:SCHEMASV:SCHEMAV_ELEMENT_CONTENT: Element '{http://www.egem.nl/StUF/sector/zkn/0310}medewerkeridentificatie': This element is not expected. Expected is ( {http://www.egem.nl/StUF/sector/zkn/0310}identificatie ).</ns0:details>
              </ns0:body>
            </ns0:Fo02Bericht>
          </detail>
        </soap11env:Fault>
      </soap11env:Body>
    </soap11env:Envelope>
    """

    message = response.text
    if response.headers["content-type"].startswith("text/html"):
        message = response.status
    else:
        try:
            xml = etree.fromstring(response.text.encode("utf8"))
            faults = xml.xpath(
                "/soapenv:Envelope/soapenv:Body/soapenv:Fault", namespaces=nsmap
            )
            if faults:
                messages = []
                for fault in faults:
                    messages.append(
                        etree.tostring(fault, pretty_print=True, encoding="unicode")
                    )
                message = "\n".join(messages)
        except etree.XMLSyntaxError:
            pass

    return message
