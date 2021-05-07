import base64
import json
import os
import uuid
from collections import OrderedDict
from datetime import timedelta
from io import StringIO
from typing import Tuple

from django.core.serializers.json import DjangoJSONEncoder
from django.template import loader
from django.utils import dateformat, timezone
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
        # ("soap11env", "http://schemas.xmlsoap.org/soap/envelope/"), # ugly
        ("soapenv", "http://schemas.xmlsoap.org/soap/envelope/"),  # added
    )
)

SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "vendor", "Zaak_DocumentServices_1_1_02"
)


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

    def _get_request_base_context(self):
        return {
            "created": timezone.now(),
            "expired": timezone.now() + timedelta(minutes=5),
            "username": self.service.user,
            "password": self.service.password,
            "zender_organisatie": self.service.zender_organisatie,
            "zender_applicatie": self.service.zender_applicatie,
            "ontvanger_organisatie": self.service.ontvanger_organisatie,
            "ontvanger_applicatie": self.service.ontvanger_applicatie,
            "referentienummer": str(uuid.uuid4()),
            "tijdstip_bericht": dateformat.format(timezone.now(), "YmdHis"),
        }

    def _wrap_soap_envelope(self, xml_str: str) -> str:
        return loader.render_to_string(
            "stuf_zds/soap/envelope.xml", {"content": mark_safe(xml_str)}
        )

    def _load_schema(self, path: str):
        # TODO cache schema?
        path = os.path.join(SCHEMA_DIR, path)
        with open(path, "r") as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)
        return xmlschema

    def _make_request(
        self, template_name: str, schema_path: str, context: dict
    ) -> Tuple[Response, Element]:
        cert = (
            (self.service.certificate.path, self.service.certificate_key.path)
            if self.service.certificate and self.service.certificate_key
            else (None, None)
        )
        # xmlschema = self._load_schema(schema_path)

        request_body = loader.render_to_string(template_name, context)

        doc = etree.parse(StringIO(request_body))
        # el = (
        #     doc.getroot()
        #     .xpath(
        #         "soap:Body",
        #         namespaces={"soap": "http://schemas.xmlsoap.org/soap/envelope/"},
        #     )[0]
        #     .getchildren()[0]
        # )
        # if not xmlschema.validate(doc):
        #     raise ValidationError(xmlschema.error_log.last_error.message)

        request_data = self._wrap_soap_envelope(request_body)

        response = requests.post(
            self.service.url,
            data=request_data,
            headers=self._get_headers(),
            cert=cert,
        )
        # TODO error handling?
        response.raise_for_status()
        return response, etree.fromstring(response.content)

    def create_zaak_identificatie(self):
        template = "stuf_zds/soap/genereerZaakIdentificatie.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context()
        response, xml = self._make_request(template, schema, context)

        zaak_identificatie = xml.xpath(
            "//zds:zaak/zkn:identificatie", namespaces=nsmap
        )[0].text

        return zaak_identificatie

    def create_zaak(self, options, zaak_identificatie):
        template = "stuf_zds/soap/creeerZaak.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
                "gemeentecode": options["gemeentecode"],
                # "zds_zaaktype_code": options['zds_zaaktype_code'],
                # "zds_zaaktype_omschrijving": options['zds_zaaktype_omschrijving'],
                "tijdstip_registratie": dateformat.format(timezone.now(), "YmdHis"),
                "datum_vandaag": dateformat.format(timezone.now(), "YmdHis"),
                "datum_eergisteren": dateformat.format(
                    timezone.now() - timedelta(days=2), "YmdHis"
                ),
            }
        )
        response, xml = self._make_request(template, schema, context)

        return None

    def create_document_identificatie(self):
        template = "stuf_zds/soap/genereerDocumentIdentificatie.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"
        context = self._get_request_base_context()
        response, xml = self._make_request(template, schema, context)

        document_identificatie = xml.xpath(
            "//zds:document/zkn:identificatie", namespaces=nsmap
        )[0].text

        return document_identificatie

    def create_zaak_document(self, options, zaak_id, doc_id, body):
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"
        schema = "zkn0310/zs-dms/zkn0310_msg_zs-dms.xsd"

        file_content = base64.b64encode(
            json.dumps(body, cls=DjangoJSONEncoder).encode()
        ).decode()

        context = self._get_request_base_context()
        context.update(
            {
                "gemeentecode": options["gemeentecode"],
                "document_omschrijving": options["omschrijving"],
                "zaak_omschrijving": options["omschrijving"],
                # "zds_zaaktype_code": options['zds_zaaktype_code'],
                # "zds_zaaktype_omschrijving": options['zds_zaaktype_omschrijving'],
                "file_content": file_content,
                "document_identificatie": doc_id,
                "zaak_identificatie": zaak_id,
                "file_name": f"file-{zaak_id}-{doc_id}",
                "tijdstip_registratie": dateformat.format(timezone.now(), "YmdHis"),
                "datum_vandaag": dateformat.format(timezone.now(), "YmdHis"),
                "datum_eergisteren": dateformat.format(
                    timezone.now() - timedelta(days=2), "YmdHis"
                ),
            }
        )
        response, xml = self._make_request(template, schema, context)

        return None
