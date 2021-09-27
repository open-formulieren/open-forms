import logging
import uuid
from datetime import timedelta

from django.template import loader
from django.utils import dateformat, timezone

import requests

from stuf.constants import EndpointType
from stuf.models import StufService

from .constants import STUF_BG_EXPIRY_MINUTES

logger = logging.getLogger(__name__)


class StufBGClient:
    def __init__(self, service: StufService):
        self.service = service

    def _get_request_base_context(self):
        referentienummer = uuid.uuid4()

        logger.debug(f"Making StUF-BG request with referentienummer {referentienummer}")

        return {
            "created": timezone.now(),
            "expires": timezone.now() + timedelta(minutes=STUF_BG_EXPIRY_MINUTES),
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

        response = requests.post(
            self.service.get_endpoint(type=EndpointType.vrije_berichten),
            data=data,
            headers={"Content-Type": "text/xml"},
            cert=self.service.get_cert(),
            auth=self.service.get_auth(),
        )

        return response

    def get_request_data(self, bsn, attributes):
        context = self._get_request_base_context()
        for attribute in attributes:
            context.update({attribute: attribute})
        context.update({"bsn": bsn})

        return loader.render_to_string("stuf_bg/StufBgRequest.xml", context)

    def get_values_for_attributes(self, bsn, attributes):

        data = self.get_request_data(bsn, attributes)

        return self._make_request(data).content
