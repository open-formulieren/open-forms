from collections import defaultdict
from collections.abc import Iterable, Sequence
from itertools import groupby

from django.conf import settings

import structlog
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)

from openforms.formio.typing.custom import SupportedChannels
from openforms.submissions.models import Submission

from .constants import (
    ADDRESS_TYPES_TO_CHANNELS,
    USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG,
)
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
                    "reference": address.get("referentie", ""),
                }
                for address in group
            ],
            "preferred": next(
                (
                    address["adres"]
                    for address in group
                    if (
                        address["isStandaardAdres"]
                        and not settings.CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS
                    )
                    or (
                        address["referentie"] == USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG
                        and settings.CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS
                    )
                ),
                None,
            ),
        }
        result.append(group_preferences)
    return result


def prepare_addresses_for_frontend(
    initial_addresses: Sequence[CommunicationChannel],
    submission: Submission,
    form_variable_key: str,
) -> Sequence[CommunicationChannelReturn]:
    """
    De-duplicate addresses and mark their verification status.
    """
    # when no data is retrieved from Open Klant we end up with initial_addresses having
    # the default value of the data type of the variable. In case we misconfigure the
    # variable and we declare it as string for example we have a wrong type here too.
    # This is coming from the `to_python` method that we use for the data types.
    if not isinstance(initial_addresses, list):
        logger.warning(
            "invalid_customer_interactions_data_type_received",
            type_received=str(type(initial_addresses)),
            submission=str(submission.uuid),
            form_variable=form_variable_key,
        )
        return []

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
