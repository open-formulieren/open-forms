import logging
from collections.abc import Mapping
from functools import partial
from typing import TypeVar

import xmltodict
from glom import glom

from openforms.logging import logevent

from ..client import BaseClient
from ..constants import EndpointType
from ..models import StufService
from ..service_client_factory import ServiceClientFactory, get_client_init_kwargs
from .constants import NAMESPACE_REPLACEMENTS, STUF_BG_EXPIRY_MINUTES
from .models import StufBGConfig

logger = logging.getLogger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


def get_client() -> "Client":
    config = StufBGConfig.get_solo()
    if not (service := config.service):
        raise NoServiceConfigured("You must configure a service!")
    return StufBGClient(service)


def StufBGClient(service: StufService) -> "Client":
    """
    Client instance factory, given a service configured in the database.
    """
    factory = ServiceClientFactory(service)
    init_kwargs = get_client_init_kwargs(
        service,
        request_log_hook=partial(logevent.stuf_bg_request, service),
        response_log_hook=partial(logevent.stuf_bg_response, service),
    )
    return Client.configure_from(factory, **init_kwargs)


class Client(BaseClient):
    sector_alias = "bg"
    soap_security_expires_minutes = STUF_BG_EXPIRY_MINUTES

    def get_values_for_attributes(self, bsn: str, attributes: list[str]) -> bytes:
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

    def get_values(self, bsn: str, attributes: list[str]) -> dict:
        response_data = self.get_values_for_attributes(bsn, attributes)

        dict_response = _remove_nils(
            xmltodict.parse(
                response_data,
                process_namespaces=True,
                namespaces=NAMESPACE_REPLACEMENTS,
                force_list=["inp.heeftAlsEchtgenootPartner", "inp.heeftAlsKinderen"],
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


# `Sequence` isn't used here at it would match str (and possibly others)
C = TypeVar("C", bound=Mapping | list)


def _remove_nils(container: C) -> C:
    """Return a copy of d with nils removed"""
    Container = type(container)  # use the same container type

    def is_nil(value):
        return isinstance(value, Mapping) and (
            value.get("@http://www.w3.org/2001/XMLSchema-instance:nil") == "true"
            or value.get("@noValue") == "geenWaarde"
        )

    return (
        Container(
            **{
                k: (_remove_nils(v) if isinstance(v, (Mapping, list)) else v)
                for k, v in container.items()
                if not is_nil(v)
            }
        )
        if issubclass(Container, Mapping)
        else [
            _remove_nils(v) if isinstance(v, (Mapping, list)) else v
            for v in container
            if not is_nil(v)
        ]
    )
