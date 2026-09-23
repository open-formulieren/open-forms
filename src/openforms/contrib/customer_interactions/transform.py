from collections import defaultdict
from collections.abc import Iterable, Sequence
from itertools import groupby

import structlog
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)

from openforms.formio.typing.custom import SupportedChannels

from .constants import ADDRESS_TYPES_TO_CHANNELS
from .typing import (
    CommunicationChannel,
    CommunicationChannelReturn,
)

logger = structlog.stdlib.get_logger(__name__)


def transform_digital_addresses(
    digital_addresses: Iterable[DigitaalAdres],
    configured_address_types: list[SupportedChannels],
) -> list[CommunicationChannel]:
    """
    Filter and group digital addresses.

    This function:
    * keeps only digital addresses listed in ``configured_address_types`` parameter.
    * groups response from ``/klantinteracties/api/v1/digitaleadressen`` endpoint by
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
            "options": [
                {
                    "address": address["adres"],
                    "verification_date": address.get("verificatieDatum"),
                }
                for address in group
            ],
            "preferred": next(
                (address["adres"] for address in group if address["isStandaardAdres"]),
                None,
            ),
        }
        result.append(group_preferences)
    return result


# TODO
# Check if we need to choose which address to keep in the case of duplicates (based on
# another key like isStandaardAdres and referentie for example)
def prepare_addresses_for_frontend(
    initial_addresses: Sequence[CommunicationChannel],
) -> Sequence[CommunicationChannelReturn]:
    """
    De-duplicate addresses and mark their verification status.
    """
    channels: list[CommunicationChannelReturn] = []
    for communication_channel in initial_addresses:
        # map of address to verification status
        addresses = defaultdict[str, bool](lambda: False)
        for option in communication_channel["options"]:
            address = option["address"]
            is_verified = addresses[address] or option["verification_date"] is not None
            addresses[option["address"]] = is_verified

        channels.append(
            {
                "type": communication_channel["type"],
                "options": [
                    {"address": address, "is_verified": is_verified}
                    for address, is_verified in addresses.items()
                ],
                "preferred": communication_channel["preferred"],
            }
        )

    return channels
