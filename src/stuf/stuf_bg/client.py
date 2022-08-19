import logging
import uuid
from datetime import timedelta
from typing import List

from django.template import loader
from django.utils import dateformat, timezone

import requests
import xmltodict

from openforms.logging.logevent import stuf_bg_request, stuf_bg_response
from stuf.constants import SOAP_VERSION_CONTENT_TYPES, EndpointType
from stuf.models import StufService

from .constants import NAMESPACE_REPLACEMENTS, STUF_BG_EXPIRY_MINUTES

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

    def make_request(self, data):
        url = self.service.get_endpoint(type=EndpointType.vrije_berichten)
        logger.debug("StUF BG client request.\nurl: %s\ndata: %s", url, data)
        stuf_bg_request(self.service, url)

        response = requests.post(
            url,
            data=data.encode("utf-8"),
            headers={
                "Content-Type": SOAP_VERSION_CONTENT_TYPES.get(
                    self.service.soap_service.soap_version
                ),
                # we only have one action so lets hardcode for now
                "SOAPAction": "http://www.egem.nl/StUF/sector/bg/0310/npsLv01",
            },
            cert=self.service.get_cert(),
            auth=self.service.get_auth(),
        )
        # TODO should this raise_for_error() ?

        logger.debug(
            "StUF BG client response.\nurl: %s\nresponse content: %s",
            url,
            response.content,
        )
        stuf_bg_response(self.service, url)

        return response

    def get_request_data(self, bsn, attributes):
        context = self._get_request_base_context()
        for attribute in attributes:
            context.update({attribute: attribute})
        context.update({"bsn": bsn})

        return loader.render_to_string("stuf_bg/StufBgRequest.xml", context)

    def get_values_for_attributes(self, bsn, attributes):

        data = self.get_request_data(bsn, attributes)

        return self.make_request(data).content

    def get_values(self, bsn: str, attributes: List[str]) -> dict:

        response_data = self.get_values_for_attributes(bsn, attributes)

        dict_response = xmltodict.parse(
            response_data,
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )

        try:
            return dict_response["Envelope"]["Body"]["npsLa01"]["antwoord"]["object"]
        except (TypeError, KeyError) as exc:
            try:
                # Get the fault information if there
                fault = dict_response["Envelope"]["Body"]["Fault"]
            except KeyError:
                fault = {}
            finally:
                logger.error(
                    "Response data has an unexpected shape",
                    extra={"response": dict_response, "fault": fault},
                    exc_info=exc,
                )
                raise exc
