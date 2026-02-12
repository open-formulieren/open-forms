from __future__ import annotations

import base64
import uuid
from collections import OrderedDict
from collections.abc import Iterator, MutableMapping
from datetime import datetime
from typing import (
    Any,
    BinaryIO,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
)

from django.core.files import File
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from json_logic.typing import Primitive
from lxml import etree
from lxml.etree import _Element
from requests import RequestException

from openforms.config.models import GlobalConfiguration
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport

from ..client import BaseClient
from ..constants import EndpointType
from ..models import StufService
from ..service_client_factory import ServiceClientFactory, get_client_init_kwargs
from ..xml import fromstring
from .constants import STUF_ZDS_EXPIRY_MINUTES
from .models import StufZDSConfig

logger = structlog.stdlib.get_logger(__name__)

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
    zds_zaaktype_code: str
    zds_zaaktype_omschrijving: NotRequired[str]
    zds_zaaktype_status_code: NotRequired[str]
    zds_zaaktype_status_omschrijving: NotRequired[str]
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
    cosigner: NotRequired[str]  # identifier of the cosigner (BSN)


class NoServiceConfigured(RuntimeError):
    pass


def get_client(options: ZaakOptions) -> Client:
    config = StufZDSConfig.get_solo()
    if not (service := config.service):
        raise NoServiceConfigured("You must configure a service!")
    return StufZDSClient(service, options, config=config)


def StufZDSClient(
    service: StufService, options: ZaakOptions, config: StufZDSConfig
) -> Client:
    factory = ServiceClientFactory(service)
    init_kwargs = get_client_init_kwargs(service)
    return Client.configure_from(
        factory,
        config=config,
        options=options,
        **init_kwargs,
    )


class ExtraData(Protocol):
    def items(self) -> Iterator[tuple[str, Primitive]]: ...


class Client(BaseClient):
    sector_alias = "zkn"
    soap_security_expires_minutes = STUF_ZDS_EXPIRY_MINUTES

    def __init__(
        self,
        *args,
        config: StufZDSConfig,
        options: ZaakOptions,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.config = config
        self.zds_options = options

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
        context["stuf_zds_config"] = self.config

        kwargs["context"] = context
        kwargs.setdefault("endpoint_type", EndpointType.vrije_berichten)

        # logging context
        _url = self.to_absolute_url(kwargs["endpoint_type"])
        structlog.contextvars.bind_contextvars(
            url=_url,
            referentienummer=context["referentienummer"],
        )

        try:
            response = self.templated_request(*args, **kwargs)
        except RequestException as exc:
            logger.error("request_failure", exc_info=exc)
            raise RegistrationFailed("error while making backend request") from exc

        if (status_code := response.status_code) < 200 or status_code >= 400:
            error_text = parse_soap_error_text(response)
            logger.error("bad_response", status_code=status_code, error_text=error_text)
            raise RegistrationFailed(
                f"error while making backend request: HTTP {status_code}: {error_text}",
                response=response,
            )

        try:
            xml = fromstring(response.content)
        except etree.XMLSyntaxError as e:
            logger.warning("bad_response", error_text="could not parse XML")
            raise RegistrationFailed(
                "error while parsing incoming backend response XML"
            ) from e

        logger.info("request_success")
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
        zaak_data: MutableMapping[str, Any],
        extra_data: ExtraData,
    ) -> None:
        now = timezone.now()
        context = {
            "tijdstip_registratie": fmt_soap_datetime(now),
            "datum_vandaag": fmt_soap_date(now),
            "zds_zaaktype_code": self.zds_options["zds_zaaktype_code"],
            "zds_zaaktype_omschrijving": self.zds_options.get(
                "zds_zaaktype_omschrijving"
            ),
            "zds_zaaktype_status_code": self.zds_options.get(
                "zds_zaaktype_status_code"
            ),
            "zds_zaaktype_status_omschrijving": self.zds_options.get(
                "zds_zaaktype_status_omschrijving"
            ),
            "zaak_omschrijving": self.zds_options["omschrijving"],
            "co_signer": self.zds_options.get("cosigner"),
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

    def set_zaak_payment(
        self,
        zaak_identificatie: str,
        partial: bool = False,
        extra: ExtraData | None = None,
    ) -> None:
        data = {
            "betalings_indicatie": (
                PaymentStatus.PARTIAL if partial else PaymentStatus.FULL
            ),
            "laatste_betaaldatum": fmt_soap_date(timezone.now()),
            "extra": extra,
        }
        self.partial_update_zaak(zaak_identificatie, data)

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
        content: File,
        doc_data: dict,
    ) -> None:
        content.seek(0)
        base64_body = base64.b64encode(content.read()).decode()

        now = timezone.now()
        # TODO: vertrouwelijkAanduiding
        context = {
            "tijdstip_registratie": fmt_soap_datetime(now),
            "datum_vandaag": fmt_soap_date(now),
            "zaak_omschrijving": self.zds_options["omschrijving"],
            "zds_documenttype_omschrijving_inzending": self.zds_options[
                "zds_documenttype_omschrijving_inzending"
            ],
            "zds_zaakdoc_vertrouwelijkheid": self.zds_options[
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
            content=submission_report.content,
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
            content=submission_attachment.content,
            doc_data={
                "titel": submission_attachment.titel
                or submission_attachment.get_display_name(),
                "bestandsnaam": submission_attachment.get_display_name(),
                "formaat": submission_attachment.content_type,
                "beschrijving": "Bijgevoegd document",
            },
        )

    def create_confirmation_email_attachment(
        self, zaak_id: str, doc_id: str, email_content: BinaryIO
    ) -> None:
        """
        Create a zaakdocument with the submitted file.
        """
        self._create_related_document(
            zaak_id=zaak_id,
            doc_id=doc_id,
            content=File(email_content),
            doc_data={
                "titel": "Bevestigingsmail",
                "bestandsnaam": "bevestigingsmail.pdf",
                "formaat": "application/pdf",
                "beschrijving": (
                    "De bevestigingsmail die naar de initiator is verstuurd."
                ),
            },
        )

    def check_config(self) -> None:
        url = f"{self.to_absolute_url(EndpointType.beantwoord_vraag)}?wsdl"
        try:
            response = self.get(url)
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
