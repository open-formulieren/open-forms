import logging
from functools import partial
from typing import List, Mapping, TypeVar

import xmltodict
from glom import glom

from openforms.logging import logevent
from soap.constants import EndpointType

from ..client import BaseClient
from ..models import StufService
from ..service_client_factory import ServiceClientFactory
from .constants import NAMESPACE_REPLACEMENTS, STUF_BG_EXPIRY_MINUTES

logger = logging.getLogger(__name__)


def StufBGClient(service: StufService) -> "Client":
    """
    Client instance factory, given a service configured in the database.
    """
    factory = ServiceClientFactory(
        service,
        request_log_hook=partial(logevent.stuf_bg_request, service),
        response_log_hook=partial(logevent.stuf_bg_response, service),
    )
    return Client.configure_from(factory)


class Client(BaseClient):
    sector_alias = "bg"
    soap_security_expires_minutes = STUF_BG_EXPIRY_MINUTES

    def get_values_for_attributes(self, bsn: str, attributes) -> bytes:
        context = {
            # replace . with _ to circumvent dot notation in template
            **{attr.replace(".", "_"): True for attr in attributes},
            "bsn": bsn,
        }
        response = self.templated_request(
            "npsLv01",
            template="stuf_bg/StufBgRequest.xml",
            context=context,
            endpoint_type=EndpointType.vrije_berichten,
        )
        return response.content

    def get_values(self, bsn: str, attributes: List[str]) -> dict:
        response_data = self.get_values_for_attributes(bsn, attributes)

        dict_response = _remove_nils(
            xmltodict.parse(
                response_data,
                process_namespaces=True,
                namespaces=NAMESPACE_REPLACEMENTS,
            )
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


M = TypeVar("M", bound=Mapping)


def _remove_nils(d: M) -> M:
    """Return a copy of d with nils removed"""
    mapping = type(d)  # use the same dict type

    def is_nil(value):
        return isinstance(value, mapping) and (
            value.get("@http://www.w3.org/2001/XMLSchema-instance:nil") == "true"
            or value.get("@noValue") == "geenWaarde"
        )

    return mapping(
        **{
            k: (_remove_nils(v) if isinstance(v, mapping) else v)
            for k, v in d.items()
            if not is_nil(v)
        }
    )
