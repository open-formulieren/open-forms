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
from openforms.submissions.models import EmailVerification, Submission
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
                    "email_address": address["adres"],
                    "verification_date": address.get("verificatieDatum"),
                }
                if address["soortDigitaalAdres"] == "email"
                else {
                    "phone_number_address": address["adres"],
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
# Remove this on Open Forms v5.0?
def transform_options(
    digital_address_data: VariableValue, submission: Submission, form_variable_key: str
) -> VariableValue:
    """
    Helper function for backwards compatibility.

    The new way of listing the options is the available addresses along with their
    verification dates (if any). This function transforms the old options to the new
    format.

    For now, only the email addresses can be verified so instead of calling the prefill
    plugin from the beginning, check our database (``EmailVerification`` model) for each
    email address and populate the options accordingly. Verification will be required if
    no verified email address is found.
    """
    assert isinstance(digital_address_data, list)

    for address in digital_address_data:
        assert isinstance(address, dict)

        if not (
            (options := address.get("options"))
            and (address_type := address.get("type"))
        ):
            logger.info(
                "profile_options_missing",
                submission_uuid=str(submission.uuid),
                form_variable_key=form_variable_key,
            )
            return digital_address_data

        assert isinstance(options, list)

        # new format of options
        if all(isinstance(option, dict) for option in options):
            # early return as we know that only the new format contains dicts for
            # both email and phone addresses
            return digital_address_data

        # old/backwards compatible format
        elif all(isinstance(option, str) for option in options):
            updated_options = []

            for option in options:
                # phone options
                if address_type == "phoneNumber":
                    # verification is not supported for phone number so we just populate
                    # the field with None
                    updated_options.append(
                        {
                            "phone_number_address": option,
                            "verification_date": None,
                        }
                    )
                # email options
                else:
                    try:
                        email_instance = EmailVerification.objects.get(email=option)
                    except EmailVerification.DoesNotExist:
                        logger.info(
                            "email_address_not_found",
                            submission_uuid=str(submission.uuid),
                            form_variable_key=form_variable_key,
                        )
                        updated_options.append(
                            {
                                "email_address": option,
                                "verification_date": None,
                            }
                        )

                        continue

                    updated_options.append(
                        {
                            "email_address": email_instance.email,
                            "verification_date": str(email_instance.verified_on.date())
                            if email_instance.verified_on
                            else None,
                        }
                    )

            address["options"] = updated_options
    return digital_address_data


# TODO
# Check if we need to choose which address to keep in the case of duplicates (based on another
# key like isStandaardAdres for example)
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

        if (
            (communication_channel := address["type"]) not in ("email", "phoneNumber")
        ) or not (options := address.get("options")):
            continue

        assert isinstance(options, list)

        for option in options:
            assert isinstance(option, dict)

            if (
                communication_channel == "email"
                and option["email_address"] not in unique_address_options
            ):
                unique_address_options[option["email_address"]] = option
            elif (
                communication_channel == "phoneNumber"
                and option["phone_number_address"] not in unique_address_options
            ):
                unique_address_options[option["phone_number_address"]] = option

        address["options"] = list(unique_address_options.values())

    return deduplicated_addresses
