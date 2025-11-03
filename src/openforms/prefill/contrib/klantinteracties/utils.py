from itertools import groupby

from openforms.contrib.klantinteracties.client import DigitaleAdres
from openforms.typing import JSONObject

from .typing import KlantInteractiesOptions

ADDRESS_OPTION_RESPONSE_VALUES: dict[str, tuple[str, str]] = {
    "email": ("emails", "preferred_email"),
    "phone_number": ("phone_numbers", "preferred_phone_number"),
}


ADDRESS_OPTION_TYPES: dict[str, str] = {
    "email": "email",
    "phone_number": "telefoonnummer",
}


def transform_digital_addresses(
    digital_addresses: list[DigitaleAdres], options: KlantInteractiesOptions
) -> JSONObject:
    """
    group and transform response from klantinteracties/api/v1/digitaleadressen endpoint
    to the DigitalAddressResponse type
    """
    sorted_addresses = sorted(digital_addresses, key=lambda x: x["soortDigitaalAdres"])
    grouped_digital_addresses = groupby(
        sorted_addresses, key=lambda x: x["soortDigitaalAdres"]
    )
    transformed_addresses = {}
    for address_type, group_iter in grouped_digital_addresses:
        group = list(group_iter)
        transformed_addresses[address_type] = {
            "all": [address["adres"] for address in group],
            "preferred": [
                address["adres"] for address in group if address["isStandaardAdres"]
            ],
        }

    result: JSONObject = {}
    for option, address_type in ADDRESS_OPTION_TYPES.items():
        if options[option] and (addresses := transformed_addresses.get(address_type)):
            response_vars = ADDRESS_OPTION_RESPONSE_VALUES[option]
            result.update(
                {
                    response_vars[0]: addresses["all"],
                    response_vars[1]: next(iter(addresses["preferred"])),
                }
            )
    return result
