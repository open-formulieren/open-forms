import structlog
from openklant_client.types.methods.maak_klant_contact import MaakKlantContactResponse

from openforms.authentication.constants import AuthAttribute
from openforms.formio.typing.custom import DigitalAddress
from openforms.prefill.contrib.customer_interactions.variables import (
    fetch_user_variable_from_profile_component,
)
from openforms.prefill.registry import register as prefill_registry
from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from .client import get_customer_interactions_client
from .constants import ADDRESS_TYPES_TO_CHANNELS

logger = structlog.stdlib.get_logger(__name__)


def update_customer_interaction_data(
    submission: Submission, profile_key: str
) -> dict[str, JSONValue] | None:
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
    """

    # submission profile data
    state = submission.load_submission_value_variables_state()
    profile_submission_data: list[DigitalAddress] = state.get_data()[profile_key]

    # prefill config
    prefill_form_variable = fetch_user_variable_from_profile_component(
        submission, profile_key
    )
    if not prefill_form_variable:
        logger.info("missing_prefill_variable", component=profile_key)
        return

    prefill_value = state.get_data()[prefill_form_variable.key]

    plugin = prefill_registry[prefill_form_variable.prefill_plugin]
    options_serializer = plugin.options(data=prefill_form_variable.prefill_options)
    options_serializer.is_valid(raise_exception=True)
    plugin_options = options_serializer.validated_data
    api_group = plugin_options["customer_interactions_api_group"]

    channels_to_address_types = {v: k for k, v in ADDRESS_TYPES_TO_CHANNELS.items()}

    # authentication
    bsn = (
        submission.auth_info.value
        if (
            submission.is_authenticated
            and submission.auth_info.attribute == AuthAttribute.bsn
        )
        else None
    )

    with get_customer_interactions_client(api_group) as client:
        if not submission.is_authenticated:
            # 1. User is not authenticated
            maak_klant_contact: MaakKlantContactResponse = (
                client.create_customer_contact(submission)
            )
            created_addresses = []
            for digital_address in profile_submission_data:
                if not (address_value := digital_address["address"]):
                    continue

                created_address = client.create_digital_address_for_betrokkene(
                    address=address_value,
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

        else:
            # user is authenticated
            party = client.find_party_for_bsn(bsn)

            if not party:
                # 2. Authenticated user isn't known in Open Klant.
                # if user wants to use provided addresses later then we save him as party
                created_party = client.create_party_for_bsn(bsn)
                # todo add to results
                party_uuid = created_party["uuid"]

                maak_klant_contact: MaakKlantContactResponse = (
                    client.create_customer_contact(submission, party_uuid=party_uuid)
                )
                created_addresses = []
                # 2a. decide to "use it once" and continue.
                # Same as flow 1 - create address and link to betrokkene
                # 2b. decide to "as new preferred" and continue
                # create address and link to party
                for digital_address in profile_submission_data:
                    created_address = client.create_digital_address(
                        address=digital_address["address"],
                        address_type=channels_to_address_types[digital_address["type"]],
                        betrokkene_uuid=maak_klant_contact["betrokkene"]["uuid"],
                        party_uuid=party_uuid
                        if digital_address.get("preferenceUpdate") == "isNewPreferred"
                        else None,
                    )
                    created_addresses.append(created_address)

                result = {
                    "klantcontact": maak_klant_contact["klantcontact"],
                    "betrokkene": maak_klant_contact["betrokkene"],
                    "onderwerpobject": maak_klant_contact["onderwerpobject"],
                    "digital_addresses": created_addresses,
                }
                return result
            else:
                # Authenticated user is known in Open Klant.
                party_uuid = party["uuid"]

                # See if there are submitted addresses not from prefill
                prefill_addresses = [address["address"] for address in prefill_value]
                new_addresses = [
                    address
                    for address in profile_submission_data
                    if address["address"] not in prefill_addresses
                ]
                maak_klant_contact: MaakKlantContactResponse = (
                    client.create_customer_contact(submission, party_uuid=party_uuid)
                )
                created_addresses = []
                # 4. Authenticated user is known in Open Klant, they have one known "digitaal adres", which is fetched.
                # They define another email address and/or phone number.
                for digital_address in new_addresses:
                    created_address = client.create_digital_address(
                        address=digital_address["address"],
                        address_type=channels_to_address_types[digital_address["type"]],
                        betrokkene_uuid=maak_klant_contact["betrokkene"]["uuid"],
                        party_uuid=party_uuid
                        if digital_address.get("preferenceUpdate") == "isNewPreferred"
                        else None,
                    )
                    created_addresses.append(created_address)

                result = {
                    "klantcontact": maak_klant_contact["klantcontact"],
                    "betrokkene": maak_klant_contact["betrokkene"],
                    "onderwerpobject": maak_klant_contact["onderwerpobject"],
                    "digital_addresses": created_addresses,
                }
                return result
