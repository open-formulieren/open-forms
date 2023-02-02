import logging
import uuid
from datetime import timedelta
from typing import List

from django.template import loader
from django.utils import dateformat, timezone

import xmltodict
from glom import glom

from openforms.logging.logevent import stuf_bg_request, stuf_bg_response
from stuf.constants import EndpointType
from stuf.models import StufService

from ..client import BaseClient
from .constants import NAMESPACE_REPLACEMENTS, STUF_BG_EXPIRY_MINUTES

logger = logging.getLogger(__name__)


class StufBGClient(BaseClient):
    sector_alias = "bg"

    def __init__(self, service: StufService):
        super().__init__(
            service,
            request_log_hook=stuf_bg_request,
            response_log_hook=stuf_bg_response,
        )

    def _get_request_base_context(self):
        referentienummer = uuid.uuid4()

        logger.debug(f"Making StUF-BG request with referentienummer {referentienummer}")

        return {
            "created": timezone.now(),
            "expires": timezone.now() + timedelta(minutes=STUF_BG_EXPIRY_MINUTES),
            "username": self.service.soap_service.user,
            "password": self.service.soap_service.password,
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

    def get_request_data(self, bsn, attributes):
        context = self._get_request_base_context()
        for attribute in attributes:
            context.update({attribute: attribute})
        context.update({"bsn": bsn})

        return loader.render_to_string("stuf_bg/StufBgRequest.xml", context)

    def get_values_for_attributes(self, bsn: str, attributes) -> bytes:
        body = self.get_request_data(bsn, attributes)
        response = self.request(
            "npsLv01",
            body=body,
            endpoint_type=EndpointType.vrije_berichten,
        )
        return response.content

    def get_values(self, bsn: str, attributes: List[str]) -> dict:

        response_data = self.get_values_for_attributes(bsn, attributes)

        dict_response = xmltodict.parse(
            response_data,
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )

        # handle missing keys/empty data graciously, see #1842
        # some include a fault response, others use an empty <antwoord /> XML element
        antwoord_object = glom(
            dict_response, "Envelope.Body.npsLa01.antwoord.object", default=None
        )
        fault = glom(dict_response, "Envelope.Body.Fault", default=None)

        # success case - we did receive a meaningful response
        if antwoord_object is not None:
            return antwoord_object

        # no fault, but also empty antwoord data -> treat this as empty response
        if fault is None:
            return {}

        # we have a fault -> log it appropriately and raise an exception
        logger.error(
            "Response data has an unexpected shape",
            extra={"response": dict_response, "fault": fault},
        )
        raise ValueError("Problem processing StUF-BG response")
