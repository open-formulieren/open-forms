import base64
import logging
import os
from collections import OrderedDict
from datetime import timedelta
from typing import Tuple

from django.template import loader
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import requests
from defusedxml.lxml import fromstring as df_fromstring
from lxml import etree
from lxml.etree import Element
from requests import RequestException, Response

from openforms.config.models import GlobalConfiguration
from openforms.logging.logevent import (
    stuf_zds_failure_response,
    stuf_zds_request,
    stuf_zds_success_response,
)
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport
from stuf.constants import (
    SOAP_VERSION_CONTENT_TYPES,
    STUF_ZDS_EXPIRY_MINUTES,
    EndpointSecurity,
    EndpointType,
)
from stuf.models import StufService

logger = logging.getLogger(__name__)

nsmap = OrderedDict(
    (
        ("zkn", "http://www.egem.nl/StUF/sector/zkn/0310"),
        ("bg", "http://www.egem.nl/StUF/sector/bg/0310"),
        ("stuf", "http://www.egem.nl/StUF/StUF0301"),
        ("zds", "http://www.stufstandaarden.nl/koppelvlak/zds0120"),
        ("gml", "http://www.opengis.net/gml"),
        ("xsi", "http://www.w3.org/2001/XMLSchema-instance"),
    )
)

SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "vendor", "Zaak_DocumentServices_1_1_02"
)
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
DATETIME_FORMAT = "%Y%m%d%H%M%S"


class PaymentStatus:
    """
    via: stuf-dms/Zaak_DocumentServices_1_1_02/zkn0310/entiteiten/zkn0310_simpleTypes.xsd

    <enumeration value="N.v.t."/>
    <enumeration value="(Nog) niet"/>
    <enumeration value="Gedeeltelijk"/>
    <enumeration value="Geheel"/>
    """

    NVT = "N.v.t."
    NOT_YET = "(Nog) niet"
    PARTIAL = "Gedeeltelijk"
    FULL = "Geheel"


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
    def __init__(self, service: StufService, options):
        """
        the options are the values from the ZaakOptionsSerializer plus 'omschrijving' and 'referentienummer'
        """
        self.service = service
        self.options = options

        self._global_config = GlobalConfiguration.get_solo()

    def _get_request_base_context(self):
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
            "tijdstip_registratie": fmt_soap_datetime(timezone.now()),
            "datum_vandaag": fmt_soap_date(timezone.now()),
            "gemeentecode": self.options["gemeentecode"],
            "zds_zaaktype_code": self.options["zds_zaaktype_code"],
            "zds_zaaktype_omschrijving": self.options["zds_zaaktype_omschrijving"],
            "zds_zaaktype_status_code": self.options["zds_zaaktype_status_code"],
            "zds_zaaktype_status_omschrijving": self.options[
                "zds_zaaktype_status_omschrijving"
            ],
            "zaak_omschrijving": self.options["omschrijving"],
            "zds_documenttype_omschrijving_inzending": self.options[
                "zds_documenttype_omschrijving_inzending"
            ],
            "referentienummer": self.options["referentienummer"],
            "global_config": self._global_config,
        }

    def _wrap_soap_envelope(self, xml_str: str) -> str:
        return loader.render_to_string(
            "stuf_zds/soap/includes/envelope.xml",
            {
                "soap_version": self.service.soap_service.soap_version,
                "soap_use_wss": (
                    self.service.soap_service.endpoint_security
                    in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth]
                ),
                "wss_username": self.service.soap_service.user,
                "wss_password": self.service.soap_service.password,
                "wss_created": fmt_soap_date(timezone.now()),
                "wss_expires": fmt_soap_date(
                    timezone.now() + timedelta(minutes=STUF_ZDS_EXPIRY_MINUTES)
                ),
                "content": mark_safe(xml_str),
            },
        )

    def _make_request(
        self,
        template_name: str,
        context: dict,
        endpoint_type,
        soap_action: str = "",
    ) -> Tuple[Response, Element]:

        request_body = loader.render_to_string(template_name, context)
        request_data = self._wrap_soap_envelope(request_body)

        url = self.service.get_endpoint(endpoint_type)

        logger.debug("SOAP-request:\n%s\n%s", url, request_data)

        try:
            stuf_zds_request(self.service, url)
            response = requests.post(
                url,
                data=request_data,
                headers={
                    "Content-Type": SOAP_VERSION_CONTENT_TYPES.get(
                        self.service.soap_service.soap_version
                    ),
                    "SOAPAction": f"http://www.egem.nl/StUF/sector/zkn/0310/{soap_action}",
                },
                auth=self.service.get_auth(),
                cert=self.service.get_cert(),
                verify=self.service.get_verify(),
            )
            if response.status_code < 200 or response.status_code >= 400:
                logger.debug("SOAP-response:\n%s", response.content)
                error_text = parse_soap_error_text(response)
                logger.error(
                    "bad response for referentienummer/submission '%s'\n%s",
                    self.options["referentienummer"],
                    error_text,
                )
                stuf_zds_failure_response(self.service, url)
                raise RegistrationFailed(
                    f"error while making backend request: HTTP {response.status_code}: {error_text}",
                    response=response,
                )
            else:
                logger.debug("SOAP-response:\n%s", response.content)
        except RequestException as e:
            logger.error(
                "bad request for referentienummer/submission '%s'",
                self.options["referentienummer"],
            )
            stuf_zds_failure_response(self.service, url)
            raise RegistrationFailed("error while making backend request") from e

        try:
            xml = df_fromstring(response.content)
        except etree.XMLSyntaxError as e:
            stuf_zds_failure_response(self.service, url)
            raise RegistrationFailed(
                "error while parsing incoming backend response XML"
            ) from e

        stuf_zds_success_response(self.service, url)

        return response, xml

    def create_zaak_identificatie(self):
        template = "stuf_zds/soap/genereerZaakIdentificatie.xml"
        context = self._get_request_base_context()
        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.vrije_berichten,
            soap_action="genereerZaakIdentificatie_Di02",
        )

        try:
            zaak_identificatie = xml_value(
                xml, "//zkn:zaak/zkn:identificatie", namespaces=nsmap
            )
        except ValueError as e:
            raise RegistrationFailed(
                "cannot find '/zaak/identificatie' in backend response"
            ) from e

        return zaak_identificatie

    def create_zaak(
        self, zaak_identificatie, zaak_data, extra_data, payment_required=False
    ):
        template = "stuf_zds/soap/creeerZaak.xml"
        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
                "extra": extra_data,
                "betalings_indicatie": (
                    PaymentStatus.NOT_YET if payment_required else PaymentStatus.NVT
                ),
            }
        )
        context.update(zaak_data)
        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
            soap_action="creeerZaak_Lk01",
        )

        return None

    def partial_update_zaak(self, zaak_identificatie: str, zaak_data: dict) -> dict:
        template = "stuf_zds/soap/updateZaak.xml"
        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
            }
        )
        context.update(zaak_data)
        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
            soap_action="updateZaak_Lk01",
        )
        return None

    def set_zaak_payment(self, zaak_identificatie: str, partial: bool = False) -> dict:
        data = {
            "betalings_indicatie": PaymentStatus.PARTIAL
            if partial
            else PaymentStatus.FULL,
            "laatste_betaaldatum": fmt_soap_date(timezone.now()),
        }
        return self.partial_update_zaak(zaak_identificatie, data)

    def create_document_identificatie(self):
        template = "stuf_zds/soap/genereerDocumentIdentificatie.xml"
        context = self._get_request_base_context()
        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.vrije_berichten,
            soap_action="genereerDocumentIdentificatie_Di02",
        )

        try:
            document_identificatie = xml_value(
                xml, "//zkn:document/zkn:identificatie", namespaces=nsmap
            )
        except ValueError as e:
            raise RegistrationFailed(
                "cannot find '/document/identificatie' in backend response"
            ) from e

        return document_identificatie

    def create_zaak_document(
        self, zaak_id: str, doc_id: str, submission_report: SubmissionReport
    ) -> None:
        """
        Create a zaakdocument with the submitted data as PDF.

        NOTE: this requires that the report was generated before the submission is
        being registered. See
        :meth:`openforms.submissions.api.viewsets.SubmissionViewSet._complete` where
        celery tasks are chained to guarantee this.
        """
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"

        submission_report.content.seek(0)

        base64_body = base64.b64encode(submission_report.content.read()).decode()

        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_id,
                "document_identificatie": doc_id,
                # TODO: Pass submission object, extract name.
                # "titel": name,
                "titel": "inzending",
                "auteur": "open-forms",
                "taal": "nld",
                "inhoud": base64_body,
                "status": "definitief",
                "bestandsnaam": f"open-forms-inzending.pdf",
                # TODO: Use name in filename
                # "bestandsnaam": f"open-forms-{name}.pdf",
                "formaat": "application/pdf",
                "beschrijving": "Ingezonden formulier",
            }
        )

        # TODO: vertrouwelijkAanduiding

        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
            soap_action="voegZaakdocumentToe_Lk01",
        )

        return None

    def create_zaak_attachment(
        self, zaak_id: str, doc_id: str, submission_attachment: SubmissionFileAttachment
    ) -> None:
        """
        Create a zaakdocument with the submitted file.
        """
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"

        submission_attachment.content.seek(0)

        base64_body = base64.b64encode(submission_attachment.content.read()).decode()

        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_id,
                "document_identificatie": doc_id,
                "titel": "bijlage",
                "auteur": "open-forms",
                "taal": "nld",
                "inhoud": base64_body,
                "status": "definitief",
                "bestandsnaam": submission_attachment.get_display_name(),
                "formaat": submission_attachment.content_type,
                "beschrijving": "Bijgevoegd document",
            }
        )

        response, xml = self._make_request(
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
            soap_action="voegZaakdocumentToe_Lk01",
        )

        return None

    def check_config(self):
        template = "stuf_zds/soap/geefZaakDetails_check.xml"
        context = self._get_request_base_context()

        try:
            self._make_request(
                template,
                context,
                endpoint_type=EndpointType.beantwoord_vraag,
                soap_action="geefZaakdetails_ZakLv01",
            )
        except RegistrationFailed as e:
            if not e.response:
                raise InvalidPluginConfiguration(
                    _("Invalid response: {exception}").format(exception=e)
                )
            else:
                try:
                    xml = df_fromstring(e.response.content)
                except etree.XMLSyntaxError as e:
                    raise InvalidPluginConfiguration(
                        _("XMLSyntaxError in error response: {exception}").format(
                            exception=e
                        )
                    )
                else:
                    faults = xml.xpath("//*[local-name()='Fault']/faultstring")
                    if not faults:
                        raise InvalidPluginConfiguration(
                            _(
                                "Unexpected response: expected 'Fault' node in SOAP response"
                            )
                        )
                    elif faults[0].text != "Object niet gevonden":
                        raise InvalidPluginConfiguration(
                            _(
                                "Unexpected response: expected '{message}' SOAP response"
                            ).format(message="Object niet gevonden")
                        )


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
    if response.headers.get("content-type", "").startswith("text/html"):
        message = response.status_code
    else:
        try:
            xml = df_fromstring(response.text.encode("utf8"))
            faults = xml.xpath("//*[local-name()='Fault']", namespaces=nsmap)
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
