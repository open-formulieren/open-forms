from collections.abc import Iterable, Mapping
from itertools import groupby

from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)

from .typing import (
    CommunicationChannel,
    SupportedChannels,
)

ADDRESS_TYPES_TO_CHANNELS: Mapping[SoortDigitaalAdres, SupportedChannels] = {
    "email": "email",
    "telefoonnummer": "phoneNumber",
}


def transform_digital_addresses(
    digital_addresses: Iterable[DigitaalAdres],
    configured_address_types: list[SupportedChannels],
) -> list[CommunicationChannel]:
    """
    Filter and group digital addresses.

    This function:
    * keeps only digital addresses listed in 'configured_address_types' parameter.
    * groups response from /klantinteracties/api/v1/digitaleadressen endpoint by
    the address type.
    """
    sorted_addresses = sorted(digital_addresses, key=lambda x: x["soortDigitaalAdres"])
    grouped_digital_addresses: groupby[SoortDigitaalAdres, DigitaalAdres] = groupby(
        sorted_addresses, key=lambda x: x["soortDigitaalAdres"]
    )

    result: list[CommunicationChannel] = []
    for address_type, group_iter in grouped_digital_addresses:
        group = list(group_iter)
        channel_name: SupportedChannels = ADDRESS_TYPES_TO_CHANNELS[address_type]
        if channel_name not in configured_address_types:
            continue

        group_preferences: CommunicationChannel = {
            "type": channel_name,
            "options": [address["adres"] for address in group],
            "preferred": next(
                (address["adres"] for address in group if address["isStandaardAdres"]),
                None,
            ),
        }
        result.append(group_preferences)
    return result
