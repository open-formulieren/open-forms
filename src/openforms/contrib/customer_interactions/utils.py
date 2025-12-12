from collections.abc import Iterable, Mapping
from itertools import groupby

import structlog
from openklant_client.types.methods.maak_klant_contact import MaakKlantContactResponse
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.customer_interactions.client import (
    get_customer_interactions_client,
)
from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.formio.typing.custom import DigitalAddress
from openforms.forms.models import FormVariable
from openforms.prefill.contrib.customer_interactions.typing import (
    CommunicationChannel,
    SupportedChannels,
)
from openforms.submissions.models import Submission
from openforms.typing import JSONValue
from openforms.variables.constants import FormVariableSources

logger = structlog.stdlib.get_logger(__name__)

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


def update_customer_interaction_data(
    submission: Submission, profile_key: str
) -> dict[str, JSONValue] | None:
    """
    Writes to the Customer interaction API when the form with profile component is submitted

    * always create contactMoment, betrokkene and onderwerpObject
    * There are several flows depending on if the user and their digital addresses
    is known in the API
    """
    # bsn
    bsn = (
        submission.auth_info.value
        if (
            submission.is_authenticated
            and submission.auth_info.attribute == AuthAttribute.bsn
        )
        else None
    )

    # submission profile data
    state = submission.load_submission_value_variables_state()
    profile_submission_data: list[DigitalAddress] = state.get_data()[profile_key]

    # prefill info
    try:
        prefill_form_variable = submission.form.formvariable_set.get(
            source=FormVariableSources.user_defined,
            prefill_plugin="communication_preferences",  # todo replace with plugin identifier
            prefill_options__profile_form_variable=profile_key,
        )
    except FormVariable.DoesNotExist:
        # todo warning, since the component configured shouldUpdateCustomerData = True
        return

    api_group_id = prefill_form_variable.prefill_options[
        "customer_interactions_api_group"
    ]
    api_group = CustomerInteractionsAPIGroupConfig.objects.get(identifier=api_group_id)
    channels_to_address_types = {v: k for k, v in ADDRESS_TYPES_TO_CHANNELS.items()}

    with get_customer_interactions_client(api_group) as client:
        if not bsn:
            # 1. Anonymous user provides email address and/or phone number.
            # We create new betrokkene, klantcontact and OnderwerpObject
            # Next we create the digital address and connect them to the previously created betrokkene
            maak_klant_contact: MaakKlantContactResponse = (
                client.create_customer_contact(submission)
            )
            created_addresses = []
            for digital_address in profile_submission_data:
                created_address = client.create_digital_address_for_betrokkene(
                    address=digital_address["address"],
                    address_type=channels_to_address_types[digital_address["type"]],
                    betrokkene_uuid=maak_klant_contact["betrokkene"]["uuid"],
                )
                created_addresses.append(created_address)

            result = {
                "klantcontact": maak_klant_contact["klantcontact"],
                "betrokkene": maak_klant_contact["betrokkene"],
                "onderwerpobject": maak_klant_contact["onderwerpobject"],
                "digital_addresses": created_addresses,
            }
            return result
