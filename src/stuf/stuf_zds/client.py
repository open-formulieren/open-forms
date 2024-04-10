import base64
import logging
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Literal, TypedDict

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import requests
from lxml import etree
from lxml.etree import _Element
from requests import RequestException

from openforms.config.models import GlobalConfiguration
from openforms.logging import logevent
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport
from soap.constants import STUF_ZDS_EXPIRY_MINUTES, EndpointType

from ..client import BaseClient
from ..models import StufService
from ..xml import fromstring

logger = logging.getLogger(__name__)

nsmap = OrderedDict(
    (
        ("zkn", "http://www.egem.nl/StUF/sector/zkn/0310"),
        ("bg", "http://www.egem.nl/StUF/sector/bg/0310"),
        ("stuf", "http://www.egem.nl/StUF/StUF0301"),
        ("zds", "http://www.stufstandaarden.nl/koppelvlak/zds0120"),
        ("gml", "http://www.opengis.net/gml"),
        ("xsi", "http://www.w3.org/2001/XMLSchema-instance"),
        ("xmime", "http://www.w3.org/2005/05/xmlmime"),
    )
)


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


def fmt_soap_datetime(value: datetime):
    return value.strftime("%Y%m%d%H%M%S")


def fmt_soap_date(value: datetime):
    return value.strftime("%Y%m%d")


def xml_value(xml, xpath, namespaces=nsmap):
    elements = xml.xpath(xpath, namespaces=namespaces)
    if len(elements) == 1:
        return elements[0].text
    else:
        raise ValueError(f"xpath not found {xpath}")


class ZaakOptions(TypedDict):
    # from stuf_zds.plugin.ZaakOptionsSerializer
    gemeentecode: str  # unused?? can't find any template using this
    zds_zaaktype_code: str
    zds_zaaktype_omschrijving: str
    zds_zaaktype_status_code: str
    zds_zaaktype_status_omschrijving: str
    zds_documenttype_omschrijving_inzending: str
    zds_zaakdoc_vertrouwelijkheid: Literal[
        "ZEER GEHEIM",
        "GEHEIM",
        "CONFIDENTIEEL",
        "VERTROUWELIJK",
        "ZAAKVERTROUWELIJK",
        "INTERN",
        "BEPERKT OPENBAAR",
        "OPENBAAR",
    ]
    # extra's
    omschrijving: str
    referentienummer: str


class StufZDSClient(BaseClient):
    sector_alias = "zkn"
    soap_security_expires_minutes = STUF_ZDS_EXPIRY_MINUTES

    def __init__(self, service: StufService, options: ZaakOptions):
        """
        Initialize the client instance.

        :arg options: Values from the ``ZaakOptionsSerializer``, amended with
          'omschrijving' and 'referentienummer'.
        """
        super().__init__(
            service,
            request_log_hook=logevent.stuf_zds_request,
        )
        self.options = options

    def execute_call(self, *args, **kwargs) -> _Element:
        """
        Method actual performing the SOAP call, with error handling.

        This essentially wraps around templated_request, but returns the parsed XML
        or raises the relevant exceptions.

        .. todo:: this can be reworked further to decouple it from our registration
           backend semantics.
        """
        # we need to pull some things out of the context for logging that may or may
        # not necessarily be set by the caller.
        context = kwargs.get("context") or {}
        context.setdefault("referentienummer", uuid.uuid4())

        kwargs["context"] = context
        kwargs.setdefault("endpoint_type", EndpointType.vrije_berichten)

        # logging context
        ref_nr = context["referentienummer"]
        endpoint_type = kwargs["endpoint_type"]
        _url = self.service.get_endpoint(type=endpoint_type)

        try:
            response = self.templated_request(*args, **kwargs)
        except RequestException as e:
            logger.error(
                "bad request for referentienummer '%s'",
                ref_nr,
                extra={"ref_nr": ref_nr},
            )
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed("error while making backend request") from e

        if (status_code := response.status_code) < 200 or status_code >= 400:
            error_text = parse_soap_error_text(response)
            logger.error(
                "bad response for referentienummer '%s'\n%s",
                ref_nr,
                error_text,
                extra={"ref_nr": ref_nr},
            )
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed(
                f"error while making backend request: HTTP {status_code}: {error_text}",
                response=response,
            )

        try:
            xml = fromstring(response.content)
        except etree.XMLSyntaxError as e:
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed(
                "error while parsing incoming backend response XML"
            ) from e

        logevent.stuf_zds_success_response(self.service, _url)
        return xml

    def create_zaak_identificatie(self) -> str:
        xml = self.execute_call(
            soap_action="genereerZaakIdentificatie_Di02",
            template="stuf_zds/soap/genereerZaakIdentificatie.xml",
            endpoint_type=EndpointType.vrije_berichten,
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
        self,
        zaak_identificatie: str,
        zaak_data: dict,
        extra_data,
    ) -> None:
        now = timezone.now()
        context = {
            "tijdstip_registratie": fmt_soap_datetime(now),
            "datum_vandaag": fmt_soap_date(now),
            "zds_zaaktype_code": self.options["zds_zaaktype_code"],
            "zds_zaaktype_omschrijving": self.options.get("zds_zaaktype_omschrijving"),
            "zds_zaaktype_status_code": self.options.get("zds_zaaktype_status_code"),
            "zds_zaaktype_status_omschrijving": self.options.get(
                "zds_zaaktype_status_omschrijving"
            ),
            "zaak_omschrijving": self.options["omschrijving"],
            "zaak_identificatie": zaak_identificatie,
            "extra": extra_data,
            "global_config": GlobalConfiguration.get_solo(),
            **zaak_data,
        }
        self.execute_call(
            soap_action="creeerZaak_Lk01",
            template="stuf_zds/soap/creeerZaak.xml",
            context=context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def partial_update_zaak(self, zaak_identificatie: str, zaak_data: dict) -> None:
        context = {
            "zaak_identificatie": zaak_identificatie,
            **zaak_data,
        }
        self.execute_call(
            soap_action="updateZaak_Lk01",
            template="stuf_zds/soap/updateZaak.xml",
            context=context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def set_zaak_payment(self, zaak_identificatie: str, partial: bool = False) -> dict:
        data = {
            "betalings_indicatie": (
                PaymentStatus.PARTIAL if partial else PaymentStatus.FULL
            ),
            "laatste_betaaldatum": fmt_soap_date(timezone.now()),
        }
        return self.partial_update_zaak(zaak_identificatie, data)

    def create_document_identificatie(self) -> str:
        xml = self.execute_call(
            soap_action="genereerDocumentIdentificatie_Di02",
            template="stuf_zds/soap/genereerDocumentIdentificatie.xml",
            endpoint_type=EndpointType.vrije_berichten,
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

    def _create_related_document(
        self,
        zaak_id: str,
        doc_id: str,
        document: SubmissionReport | SubmissionFileAttachment,
        doc_data: dict,
    ) -> None:
        document.content.seek(0)
        base64_body = base64.b64encode(document.content.read()).decode()

        now = timezone.now()
        # TODO: vertrouwelijkAanduiding
        context = {
            "tijdstip_registratie": fmt_soap_datetime(now),
            "datum_vandaag": fmt_soap_date(now),
            "zaak_omschrijving": self.options["omschrijving"],
            "zds_documenttype_omschrijving_inzending": self.options[
                "zds_documenttype_omschrijving_inzending"
            ],
            "zds_zaakdoc_vertrouwelijkheid": self.options[
                "zds_zaakdoc_vertrouwelijkheid"
            ],
            "zaak_identificatie": zaak_id,
            "document_identificatie": doc_id,
            "auteur": "open-forms",
            "taal": "nld",
            "inhoud": base64_body,
            "status": "definitief",
            **doc_data,
        }
        self.execute_call(
            soap_action="voegZaakdocumentToe_Lk01",
            template="stuf_zds/soap/voegZaakdocumentToe.xml",
            context=context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

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
        self._create_related_document(
            zaak_id=zaak_id,
            doc_id=doc_id,
            document=submission_report,
            doc_data={
                # TODO: Pass submission object, extract name.
                # "titel": name,
                "titel": "inzending",
                # TODO: Use name in filename
                # "bestandsnaam": f"open-forms-{name}.pdf",
                "bestandsnaam": "open-forms-inzending.pdf",
                "formaat": "application/pdf",
                "beschrijving": "Ingezonden formulier",
            },
        )

    def create_zaak_attachment(
        self, zaak_id: str, doc_id: str, submission_attachment: SubmissionFileAttachment
    ) -> None:
        """
        Create a zaakdocument with the submitted file.
        """
        self._create_related_document(
            zaak_id=zaak_id,
            doc_id=doc_id,
            document=submission_attachment,
            doc_data={
                "titel": "bijlage",
                "bestandsnaam": submission_attachment.get_display_name(),
                "formaat": submission_attachment.content_type,
                "beschrijving": "Bijgevoegd document",
            },
        )

    def check_config(self) -> None:
        url = f"{self.service.get_endpoint(EndpointType.beantwoord_vraag)}?wsdl"
        auth_kwargs = self._get_auth_kwargs()
        try:
            response = requests.get(url, **auth_kwargs)
            if not response.ok:
                error_text = parse_soap_error_text(response)
                raise InvalidPluginConfiguration(
                    f"Error while making backend request: HTTP {response.status_code}: {error_text}",
                )
        except RequestException as e:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
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
            xml = fromstring(response.text.encode("utf8"))
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
