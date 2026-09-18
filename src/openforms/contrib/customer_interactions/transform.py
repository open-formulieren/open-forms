from collections.abc import Iterable, Sequence
from copy import deepcopy
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
    configured_address_types: Sequence[SupportedChannels],
) -> Sequence[CommunicationChannel]:
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


def normalized_data_for_frontend(
    addresses: Sequence[CommunicationChannel],
) -> Sequence[CommunicationChannelReturn]:
    """
    Normalize the addresses before sending them to frontend.

    The frontend accepts addresses that can be considered as verified or not. So we need
    to return the same result but instead of the whole detailed verification date, we
    send whether it's verified or not.
    """
    return [
        {
            **address,
            "options": [
                {
                    "address": option["address"],
                    "is_verified": bool(option["verification_date"]),
                }
                for option in address["options"]
            ],
        }
        for address in addresses
    ]


# TODO
# Check if we need to choose which address to keep in the case of duplicates (based on
# another key like isStandaardAdres for example)
def filter_duplicate_addresses(
    initial_addresses: Sequence[CommunicationChannel],
) -> Sequence[CommunicationChannelReturn]:
    """
    Helper function to de-duplicate addresses.

    Given a list of digital addresses remove all the duplicates (both emails and phones)
    and return the most suitable one. The address with a verification date always takes
    precedence when available.

    """
    assert isinstance(initial_addresses, list)
    deduplicated_addresses = deepcopy(initial_addresses)

    for address in deduplicated_addresses:
        unique_address_options = {}
        assert isinstance(address, dict)

        options = address["options"]
        assert isinstance(options, list)
        for option in options:
            assert isinstance(option, dict)

            cur_address = option["address"]
            cur_verified = bool(option["verification_date"])

            existing = unique_address_options.get(cur_address)

            if existing is None:
                unique_address_options[cur_address] = option
                continue

            existing_verified = bool(existing["verification_date"])

            # prioritize verified address
            if cur_verified and not existing_verified:
                unique_address_options[cur_address] = option

        address["options"] = list(unique_address_options.values())

    result = normalized_data_for_frontend(deduplicated_addresses)
    return result
