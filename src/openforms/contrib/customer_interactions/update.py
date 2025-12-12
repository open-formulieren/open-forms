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

    prefill_addresses = state.get_data()[prefill_form_variable.key]

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

    result = {}
    with get_customer_interactions_client(api_group) as client:
        if bsn:  # todo use submission.is_authenticated and case match
            # link authenticated user to the party
            party = client.find_party_for_bsn(bsn)
            if not party:
                party = client.create_party_for_bsn(bsn)
                result["party"] = party

            party_uuid = party["uuid"]
        else:
            party_uuid = None

        maak_klant_contact: MaakKlantContactResponse = client.create_customer_contact(
            submission, party_uuid
        )

        created_addresses = []
        for digital_address in profile_submission_data:
            if digital_address["address"] in prefill_addresses:
                # used value from prefill, so it already exists in Open Klant
                continue

            created_address = client.create_digital_address(
                address=digital_address["address"],
                address_type=channels_to_address_types[digital_address["type"]],
                betrokkene_uuid=maak_klant_contact["betrokkene"]["uuid"],
                party_uuid=party_uuid
                if digital_address.get("preferenceUpdate") == "isNewPreferred"
                else None,
            )
            created_addresses.append(created_address)

        result.update(
            {
                "klantcontact": maak_klant_contact["klantcontact"],
                "betrokkene": maak_klant_contact["betrokkene"],
                "onderwerpobject": maak_klant_contact["onderwerpobject"],
                "digital_addresses": created_addresses,
            }
        )
        return result
