from typing import TypedDict

from django.contrib.auth.hashers import check_password as check_salted_hash
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from requests import RequestException

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission
from openforms.validations.registry import register

from .client import NoServiceConfigured, SearchParams, get_client


class AddressValue(TypedDict, total=False):
    postcode: str
    houseNumber: str
    houseLetter: str
    houseNumberAddition: str


@register(
    "brk-Zaakgerechtigde",
    verbose_name=_("BRK - Zaakgerechtigde"),
    for_components=("address",),
)
@deconstructible
class BRKZaakgerechtigdeValidator:

    error_messages = {
        "no_bsn": _("No BSN is available to validate your address."),
        "retrieving_error": _(
            "There was an error while retrieving the available properties. Please try again later"
        ),
        "not_owner": _("You are not one of the registered owners of this property"),
        "multiple_cadastrals": _("We couldn't accurately determine your properties"),
        "not_found": _("No property found for this address."),
    }

    def __call__(self, value: AddressValue, submission: Submission) -> bool:

        try:
            client = get_client()
        except NoServiceConfigured as e:
            raise ValidationError(self.error_messages["retrieving_error"]) from e

        address_query: SearchParams = {
            "postcode": value["postcode"],
            "huisnummer": value["houseNumber"],
        }
        if "houseLetter" in value:
            address_query["huisletter"] = value["houseLetter"]
        if "houseNumberAddition" in value:
            address_query["huisnummertoevoeging"] = value["houseNumberAddition"]

        # We assume submission has auth_info available, should we verify that this validator is used
        # on a step that requires login?
        if submission.auth_info.attribute != AuthAttribute.bsn:
            raise ValidationError(self.error_messages["no_bsn"])

        try:
            with client:
                cadastrals_resp = client.get_cadastrals_by_address(address_query)
                kadastraals = cadastrals_resp["_embedded"]["kadastraalOnroerendeZaken"]
                if len(kadastraals) > 1:
                    # The query by address returned more than one cadastral, this shouldn't happen
                    raise ValidationError(self.error_messages["multiple_cadastrals"])
                if not kadastraals:
                    raise ValidationError(self.error_messages["not_found"])
                kadastraal_id = kadastraals[0]["identificatie"]

                titleholders_resp = client.get_cadastral_titleholders_by_cadastral_id(
                    kadastraal_id
                )

                bsns = [
                    a["persoon"]["identificatie"]
                    for a in titleholders_resp["_embedded"]["zakelijkGerechtigden"]
                ]
                if submission.auth_info.attribute_hashed:
                    is_valid = any(
                        check_salted_hash(bsn, submission.auth_info.value)
                        for bsn in bsns
                    )
                else:
                    is_valid = submission.auth_info.value in bsns

                if not is_valid:
                    raise ValidationError(self.error_messages["not_owner"])

        except (RequestException, KeyError, TypeError) as e:
            raise ValidationError(self.error_messages["retrieving_error"]) from e

        return True
