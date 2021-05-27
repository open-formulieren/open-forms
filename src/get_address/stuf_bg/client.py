import logging
import uuid
from datetime import timedelta

from django.template import loader
from django.utils import dateformat, timezone

import requests

from stuf.models import SoapService

from .constants import STUF_BG_EXPIRY_MINUTES

logger = logging.getLogger(__name__)


class StufBGClient:
    def __init__(self, service: SoapService):
        self.service = service

    def _get_request_base_context(self):
        referentienummer = uuid.uuid4()

        logger.debug(f"Making StUF-BG request with referentienummer {referentienummer}")

        return {
            "created": timezone.now(),
            "expired": timezone.now() + timedelta(minutes=STUF_BG_EXPIRY_MINUTES),
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
            "referentienummer": referentienummer,
            "tijdstip_bericht": dateformat.format(timezone.now(), "YmdHis"),
        }

    def _make_request(self, data):

        # TODO Move this validation to a unit test
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
            headers={"Content-Type": "application/soap+xml"},
            cert=self.service.get_cert(),
            auth=(self.service.user, self.service.password),
        )

        return response

    def get_address_request_data(self, bsn):
        context = self._get_request_base_context()
        context.update({"bsn": bsn})

        template = "get_address/stuf_bg/templates/RequestAddress.xml"

        return loader.render_to_string(template, context)

    # TODO should be generic and where this is called should pass in the
    #   attributes to get
    def get_address(self, bsn):

        data = self.get_address_request_data(bsn)

        return self._make_request(data).content
