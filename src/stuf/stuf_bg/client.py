from collections.abc import Mapping
from functools import partial
from typing import Literal

import structlog
import xmltodict
from glom import glom

from openforms.logging import logevent

from ..client import BaseClient
from ..constants import EndpointType
from ..models import StufService
from ..service_client_factory import ServiceClientFactory, get_client_init_kwargs
from .constants import (
    NAMESPACE_REPLACEMENTS,
    STUF_BG_EXPIRY_MINUTES,
)
from .data import NaturalPersonDetails
from .models import StufBGConfig
from .utils import normalize_date_of_birth

logger = structlog.stdlib.get_logger(__name__)


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

    def get_values_for_attributes(
        self,
        bsn: str,
        attributes: list[str],
        template: str = "stuf_bg/StufBgRequest.xml",
    ) -> bytes:
        context = {
            # replace . with _ to circumvent dot notation in template
            **{attr.replace(".", "_"): True for attr in attributes},
            "bsn": bsn,
        }
        response = self.templated_request(
            "npsLv01",
            template=template,
            context=context,
            endpoint_type=EndpointType.vrije_berichten,
        )
        return response.content

    def get_values(self, bsn: str, attributes: list[str]) -> dict:
        structlog.contextvars.bind_contextvars(requested_attributes=attributes)
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
            logger.info("received_response_object")
            return antwoord_object

        # no fault, but also empty antwoord data -> treat this as empty response
        if fault is None:
            logger.info("received_empty_response")
            return {}

        # we have a fault -> log it appropriately and raise an exception
        logger.error("received_fault_response", response=dict_response, fault=fault)
        raise ValueError("Problem processing StUF-BG response")

    def get_partners_or_children(
        self,
        bsn: str,
        attribute: str,
        relation: Literal["partners", "children"],
        include_deceased: bool = True,
    ) -> list[NaturalPersonDetails]:
        context = {"bsn": bsn}
        response = self.templated_request(
            "npsLv01",
            template=f"stuf_bg/{relation.capitalize()}StufBgRequest.xml",
            context=context,
            endpoint_type=EndpointType.vrije_berichten,
        )

        dict_response = _remove_nils(
            xmltodict.parse(
                response.content,
                process_namespaces=True,
                namespaces=NAMESPACE_REPLACEMENTS,
                force_list=attribute,
            )
        )
        # some include a fault response, others use an empty <antwoord /> XML element
        response_obj = glom(
            dict_response, "Envelope.Body.npsLa01.antwoord.object", default=None
        )

        fault = glom(dict_response, "Envelope.Body.Fault", default=None)

        # success case - we did receive a meaningful response
        if response_obj is not None:
            members = response_obj.get(attribute)
            members_data: list[NaturalPersonDetails] = [
                NaturalPersonDetails(
                    bsn=member["gerelateerde"].get("inp.bsn") or "",
                    first_names=member["gerelateerde"].get("voornamen") or "",
                    initials=member["gerelateerde"].get("voorletters") or "",
                    affixes=member["gerelateerde"].get("voorvoegselGeslachtsnaam")
                    or "",
                    last_name=member["gerelateerde"].get("geslachtsnaam") or "",
                    date_of_birth=(
                        normalize_date_of_birth(
                            member["gerelateerde"].get("geboortedatum")
                        )
                        if member["gerelateerde"].get("geboortedatum")
                        else ""
                    ),
                    # Add 'deceased' flag only if relation == "children"
                    **(
                        {
                            "deceased": bool(
                                member["gerelateerde"].get("overlijdensdatum")
                            )
                        }
                        if relation == "children"
                        else {}
                    ),
                )
                for member in members
                if "gerelateerde" in member
            ]

            if include_deceased is False:
                members_data = [
                    member for member in members_data if not member.deceased
                ]

            return members_data

        # no fault, but also empty antwoord data -> treat this as empty response
        if fault is None:
            return []

        # we have a fault -> log it appropriately and raise an exception
        logger.error(
            "stuf_bg.unexpected_response_shape",
            response=dict_response,
            fault=fault,
        )
        raise ValueError("Problem processing StUF-BG response")


# `Sequence` isn't used here at it would match str (and possibly others)
def _remove_nils[C: Mapping | list](container: C) -> C:
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
                k: (_remove_nils(v) if isinstance(v, Mapping | list) else v)
                for k, v in container.items()
                if not is_nil(v)
            }
        )
        if issubclass(Container, Mapping)
        else [
            _remove_nils(v) if isinstance(v, Mapping | list) else v
            for v in container
            if not is_nil(v)
        ]
    )
