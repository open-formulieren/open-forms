from collections.abc import Iterable, Sequence
from copy import deepcopy
from itertools import groupby

import structlog
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)

from openforms.formio.typing.custom import SupportedChannels
from openforms.prefill.contrib.customer_interactions.typing import (
    CommunicationChannel,
)
from openforms.typing import VariableValue

from .constants import ADDRESS_TYPES_TO_CHANNELS

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
                if address["soortDigitaalAdres"] in ("email", "telefoonnummer")
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
# another key like isStandaardAdres for example)
def filter_duplicate_addresses(
    initial_addresses: VariableValue,
) -> Iterable[VariableValue]:
    """
    Helper function to de-duplicate addresses.

    Given a list of digital addresses remove all the duplicates (both emails and phones)
    and return the updated one.
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

            if option["address"] in unique_address_options:
                continue

            unique_address_options[option["address"]] = option

        address["options"] = list(unique_address_options.values())

    return deduplicated_addresses
