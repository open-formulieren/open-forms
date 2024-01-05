import logging
from contextlib import contextmanager
from typing import Iterator

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from glom import glom
from requests import RequestException
from rest_framework import serializers

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission
from openforms.validations.registry import register

from .client import NoServiceConfigured, SearchParams, get_client
from .constants import AddressValue

logger = logging.getLogger(__name__)


@contextmanager
def suppress_api_errors(error_message: str) -> Iterator[None]:
    try:
        yield
    except RequestException as e:
        logger.error(
            "An exception occured when trying to fetch the BRK API", exc_info=e
        )
        raise ValidationError(error_message) from e


class AddressValueSerializer(serializers.Serializer):
    postcode = serializers.RegexField(
        "^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
    )
    house_number = serializers.RegexField(
        r"^\d{1,5}$",
    )
    house_letter = serializers.RegexField(
        "^[a-zA-Z]$", required=False, allow_blank=True
    )
    house_number_addition = serializers.RegexField(
        "^([a-z,A-Z,0-9]){1,4}$",
        required=False,
        allow_blank=True,
    )

    def validate_postcode(self, value: str) -> str:
        """Normalize the postcode so that it matches the regex from the BRK API."""
        return value.upper().replace(" ", "")


class ValueSerializer(serializers.Serializer):
    value = AddressValueSerializer()


@register(
    "brk-zakelijk-gerechtigd",
    verbose_name=_("BRK - Zakelijk gerechtigd"),
    for_components=("addressNL",),
)
@deconstructible
class BRKZakelijkGerechtigdeValidator:

    value_serializer = ValueSerializer

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
            client = get_client()
        except NoServiceConfigured as e:
            logger.error(
                "No BRK service configured when trying to validate address data",
                exc_info=e,
            )
            raise ValidationError(self.error_messages["retrieving_error"]) from e

        address_query: SearchParams = {
            "postcode": value["postcode"],
            "huisnummer": value["house_number"],
        }
        if "house_letter" in value:
            address_query["huisletter"] = value["house_letter"]
        if "house_number_addition" in value:
            address_query["huisnummertoevoeging"] = value["house_number_addition"]

        with (client, suppress_api_errors(self.error_messages["retrieving_error"])):
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
