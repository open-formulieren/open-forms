from collections.abc import Iterator
from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

import structlog
from glom import glom
from requests import RequestException
from rest_framework import serializers

from openforms.authentication.service import AuthAttribute
from openforms.formio.components.custom import AddressValueSerializer
from openforms.submissions.models import Submission
from openforms.validations.base import BasePlugin
from openforms.validations.registry import register

from .client import NoServiceConfigured, SearchParams, get_client
from .constants import AddressValue

logger = structlog.stdlib.get_logger(__name__)

BRK_ZAKELIJK_GERECHTIGD_VALIDATOR_ID = "brk-zakelijk-gerechtigd"


@contextmanager
def suppress_api_errors(error_message: str) -> Iterator[None]:
    try:
        yield
    except RequestException as exc:
        logger.error("brk_request_failure", exc_info=exc)
        raise ValidationError(error_message) from exc


class ValueSerializer(serializers.Serializer):
    value = AddressValueSerializer()


@register("brk-zakelijk-gerechtigd")
@deconstructible
class BRKZakelijkGerechtigdeValidator(BasePlugin[AddressValue]):
    value_serializer = ValueSerializer
    verbose_name = _("BRK - Zakelijk gerechtigd")
    for_components = ("addressNL",)

    error_messages = {
        "no_bsn": _("No BSN is available to validate your address."),
        "retrieving_error": _(
            "There was an error while retrieving the available properties. Please try again later."
        ),
        "invalid": _(
            "According to our records, you are not a legal owner of this property."
        ),
        "not_found": _("No property found for this address."),
    }

    def __call__(self, value: AddressValue, submission: Submission) -> bool:
        if (
            not submission.is_authenticated
            or submission.auth_info.attribute != AuthAttribute.bsn
        ):
            raise ValidationError(self.error_messages["no_bsn"])

        assert not submission.auth_info.attribute_hashed

        try:
            client = get_client(submission=submission)
        except NoServiceConfigured as exc:
            logger.error("brk_service_not_configured", exc_info=exc)
            raise ValidationError(self.error_messages["retrieving_error"]) from exc

        address_query: SearchParams = {
            "postcode": value["postcode"],
            "huisnummer": value["houseNumber"],
        }
        if "houseLetter" in value:
            address_query["huisletter"] = value["houseLetter"]
        if "houseNumberAddition" in value:
            address_query["huisnummertoevoeging"] = value["houseNumberAddition"]

        with client, suppress_api_errors(self.error_messages["retrieving_error"]):
            real_estate_objects_resp = client.get_real_estate_by_address(address_query)
            real_estate_objects = glom(
                real_estate_objects_resp,
                "_embedded.kadastraalOnroerendeZaken",
                default=[],
            )

            if not real_estate_objects:
                raise ValidationError(self.error_messages["not_found"])
            # Sanity check if the query by address returned more than one cadastral, this shouldn't happen
            assert len(real_estate_objects) <= 1

            kadastraal_id = real_estate_objects[0]["identificatie"]

            titleholders_resp = client.get_cadastral_titleholders_by_cadastral_id(
                kadastraal_id
            )

            bsns = [
                a["persoon"]["identificatie"]
                for a in titleholders_resp["_embedded"]["zakelijkGerechtigden"]
            ]

            if submission.auth_info.value not in bsns:
                raise ValidationError(self.error_messages["invalid"])

        return True
