from collections.abc import Mapping
from typing import TypedDict

import structlog
from openklant_client.types.methods.maak_klant_contact import MaakKlantContactResponse
from openklant_client.types.resources.betrokkene import Betrokkene
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    SoortDigitaalAdres,
)
from openklant_client.types.resources.klant_contact import KlantContact
from openklant_client.types.resources.onderwerp_object import OnderwerpObject

from openforms.authentication.constants import AuthAttribute
from openforms.formio.typing.custom import DigitalAddress, SupportedChannels
from openforms.prefill.contrib.customer_interactions.typing import CommunicationChannel
from openforms.prefill.contrib.customer_interactions.variables import (
    fetch_user_variable_from_profile_component,
)
from openforms.prefill.registry import register as prefill_registry
from openforms.submissions.models import Submission

from .client import get_customer_interactions_client
from .constants import ADDRESS_TYPES_TO_CHANNELS

logger = structlog.stdlib.get_logger(__name__)


class DigitalAddressResults(TypedDict):
    created: list[DigitaalAdres]
    updated: list[DigitaalAdres]


class UpdateCustomerInteractionsResult(TypedDict):
    klantcontact: KlantContact
    betrokkene: Betrokkene
    onderwerpobject: OnderwerpObject
    digital_addresses: DigitalAddressResults
    partij_uuid: str


def update_customer_interaction_data(
    submission: Submission, profile_key: str
) -> UpdateCustomerInteractionsResult | None:
    """
    Writes to the Customer interaction API when the form with profile component is submitted.

    There are several flows how the information is updated depending on if the user and
    their digital addresses are known in the Customer Interactions API

    1. User is not authenticated (implemented):

      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject``
      * create ``digitaalAdres`` records linked to the created ``betrokkene``

    2. User is authenticated, but unknown in the API:

      * create ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the created ``partij``
      * create ``digitaalAdres`` records linked to the created ``betrokkene``. If the address is
        submitted as ``isNewPreferred``, then it's also linked to the created ``partij``

    3. User is authenticated, known in the API and uses pre-filled data:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``

    4. User is authenticated, known in the API and submits new addresses:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * create ``digitaalAdres`` records linked to the created ``betrokkene`` for the new addresses.
        If the address is submitted as ``isNewPreferred``, then it's also linked to the ``partij``

    5. User is authenticated, known in the API and submits existing addresses with the changed preference:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * if the address is submitted as ``useOnlyOnce``, then we don't update it
      * if the address is submitted as ``isNewPreferred``, and the existing address is not
        preferred (``isStandaardAdres`` == False) then we update it with ``isStandaardAdres`` = True

    """

    # submission profile data
    state = submission.load_submission_value_variables_state()
    profile_submission_data: list[DigitalAddress] = state.get_data()[profile_key]  # pyright: ignore[reportAssignmentType]

    # prefill config
    prefill_form_variable = fetch_user_variable_from_profile_component(
        submission, profile_key
    )
    if not prefill_form_variable:
        logger.info("missing_prefill_variable", component=profile_key)
        return

    prefill_value: list[CommunicationChannel] = state.get_data(include_unsaved=True)[
        prefill_form_variable.key
    ]  # pyright: ignore[reportAssignmentType]

    plugin = prefill_registry[prefill_form_variable.prefill_plugin]
    options_serializer = plugin.options(data=prefill_form_variable.prefill_options)
    options_serializer.is_valid(raise_exception=True)
    plugin_options = options_serializer.validated_data
    api_group = plugin_options["customer_interactions_api_group"]

    channels_to_address_types: Mapping[SupportedChannels, SoortDigitaalAdres] = {
        v: k for k, v in ADDRESS_TYPES_TO_CHANNELS.items()
    }

    with get_customer_interactions_client(api_group) as client:
        if submission.is_authenticated:
            auth_value = submission.auth_info.value
            auth_attribute: AuthAttribute = submission.auth_info.attribute

            # link authenticated user to the party
            party, created = client.get_or_create_party(auth_attribute, auth_value)
            party_uuid = party["uuid"]
        else:
            party_uuid = ""

        customer_contact: MaakKlantContactResponse = client.create_customer_contact(
            submission, party_uuid
        )
        assert customer_contact["betrokkene"] is not None
        assert customer_contact["onderwerpobject"] is not None

        created_addresses: list[DigitaalAdres] = []
        updated_addresses: list[DigitaalAdres] = []
        for digital_address in profile_submission_data:
            # submitted data
            address_value = digital_address["address"]
            address_channel: SupportedChannels = digital_address["type"]
            is_address_new_preferred: bool = bool(
                digital_address.get("preferenceUpdate") == "isNewPreferred"
            )
            # prefill values
            prefill_communication_channel: CommunicationChannel | None = next(
                (value for value in prefill_value if value["type"] == address_channel),
                None,
            )
            prefill_channel_options = (
                prefill_communication_channel["options"]
                if prefill_communication_channel
                else []
            )
            prefill_preferred = (
                prefill_communication_channel["preferred"]
                if prefill_communication_channel
                else None
            )

            if address_value in prefill_channel_options:
                # we update it only if it's marked as "isNewPreferred"
                if is_address_new_preferred and address_value != prefill_preferred:
                    updated_address = client.update_digital_address_for_party(
                        address=address_value, party_uuid=party_uuid, is_preferred=True
                    )
                    updated_addresses.append(updated_address)

            else:
                created_address = client.create_digital_address(
                    address=address_value,
                    address_type=channels_to_address_types[address_channel],
                    betrokkene_uuid=customer_contact["betrokkene"]["uuid"],
                    party_uuid=party_uuid if is_address_new_preferred else "",
                    is_preferred=is_address_new_preferred,
                )
                created_addresses.append(created_address)

        digital_address_results = DigitalAddressResults(
            created=created_addresses, updated=updated_addresses
        )
        result: UpdateCustomerInteractionsResult = {
            "klantcontact": customer_contact["klantcontact"],
            "betrokkene": customer_contact["betrokkene"],
            "onderwerpobject": customer_contact["onderwerpobject"],
            "digital_addresses": digital_address_results,
            "partij_uuid": party_uuid,
        }

        return result
