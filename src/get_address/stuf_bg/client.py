import base64
import uuid
from datetime import timedelta

from django.template import loader
from django.utils import dateformat, timezone

import requests

from openforms.registrations.contrib.stuf_zds.models import SoapService


class StufBGClient:
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
            "zender_administratie": self.service.zender_administratie,
            "zender_gebruiker": self.service.zender_gebruiker,
            "ontvanger_organisatie": self.service.ontvanger_organisatie,
            "ontvanger_applicatie": self.service.ontvanger_applicatie,
            "ontvanger_administratie": self.service.ontvanger_administratie,
            "ontvanger_gebruiker": self.service.ontvanger_gebruiker,
            "referentienummer": str(uuid.uuid4()),
            "tijdstip_bericht": dateformat.format(timezone.now(), "YmdHis"),
        }

    def _make_request(self, data):

        cert = (
            (self.service.certificate.path, self.service.certificate_key.path)
            if self.service.certificate and self.service.certificate_key
            else (None, None)
        )

        # TODO Add this validation?
        # with open(
        #     f"{settings.DJANGO_PROJECT_DIR}/xsd/bg0310/vraagAntwoord/bg0310_namespace.xsd",
        #     "r",
        # ) as f:
        #     xmlschema_doc = etree.parse(f)
        #     xmlschema = etree.XMLSchema(xmlschema_doc)
        #
        # doc = etree.parse(BytesIO(bytes(data, encoding="UTF-8")))
        # el = (
        #     doc.getroot()
        #     .xpath(
        #         "soap:Body",
        #         namespaces={"soap": "http://schemas.xmlsoap.org/soap/envelope/"},
        #     )[0]
        #     .getchildren()[0]
        # )
        # if not xmlschema.validate(el):
        #     raise ValidationError(xmlschema.error_log.last_error.message)

        response = requests.post(
            self.service.url,
            data=data,
            headers=self._get_headers(),
            cert=cert,
        )

        return response

    def get_address_request_data(self, bsn):
        context = self._get_request_base_context()
        context.update({"bsn": bsn})

        template = "get_address/stuf_bg/templates/RequestAddress.xml"

        return loader.render_to_string(template, context)

    def get_address(self, bsn):

        data = self.get_address_request_data(bsn)

        return self._make_request(data).content
