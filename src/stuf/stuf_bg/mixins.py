from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.template import loader
from django.utils import timezone

from lxml import etree

from stuf.models import StufService
from stuf.xml import fromstring

PATH_XSDS = (Path(settings.BASE_DIR) / "src" / "stuf" / "stuf_bg" / "xsd").resolve()
STUF_BG_XSD = PATH_XSDS / "bg0310" / "vraagAntwoord" / "bg0310_namespace.xsd"
SOAP_NS_TO_VERSION = {
    "http://schemas.xmlsoap.org/soap/envelope/": "1.1",
    "http://www.w3.org/2003/05/soap-envelope": "1.2",
}


@lru_cache
def _stuf_bg_xmlschema_doc() -> etree._ElementTree:
    # don't add the etree.XMLSchema construction to this; it's an object
    # that contains state like error_log
    with STUF_BG_XSD.open("r") as infile:
        return etree.parse(infile)


class StUFBGBaseMixin:
    """Provides helpers for StUF-BG XML documents handling."""

    @property
    def xml_schema(self) -> etree.XMLSchema:
        """Return a fresh XMLSchema object using cached parsed XSD."""
        return etree.XMLSchema(_stuf_bg_xmlschema_doc())

    def extract_soap_body(self, full_doc: str | bytes) -> etree._Element:
        """Extract the first child of the SOAP Body element."""
        doc = fromstring(full_doc)
        ns = doc.nsmap.get(doc.prefix) if doc.prefix else doc.nsmap.get(None)

        if ns not in SOAP_NS_TO_VERSION:
            raise ValueError(f"Unsupported SOAP namespace: {ns}")

        body = doc.xpath("soap:Body", namespaces={"soap": ns})[0]
        return body[0]

    def extract_soap_response(self, template_name: str, service: StufService) -> bytes:
        return bytes(
            loader.render_to_string(
                template_name,
                context={
                    "referentienummer": "38151851-0fe9-4463-ba39-416042b8f406",
                    "tijdstip_bericht": timezone.now().strftime("%Y%m%d%H%M%S"),
                    "zender_organisatie": service.zender_organisatie,
                    "zender_applicatie": service.zender_applicatie,
                    "zender_administratie": service.zender_administratie,
                    "zender_gebruiker": service.zender_gebruiker,
                    "ontvanger_organisatie": service.ontvanger_organisatie,
                    "ontvanger_applicatie": service.ontvanger_applicatie,
                    "ontvanger_administratie": service.ontvanger_administratie,
                    "ontvanger_gebruiker": service.ontvanger_gebruiker,
                },
            ),
            encoding="utf-8",
        )

    def xpath_soap_body(
        self,
        xml_body: str | bytes,
        expression: str,
        namespaces: OrderedDict[str, str],
    ) -> list[etree._Element]:
        """Run an XPath expression against the SOAP body."""
        soap_body = self.extract_soap_body(xml_body)
        return soap_body.xpath(expression, namespaces=namespaces or {})
