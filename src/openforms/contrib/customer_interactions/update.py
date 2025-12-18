import structlog
from openklant_client.types.methods.maak_klant_contact import MaakKlantContactResponse

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
      * create ``gigitaalAdres`` records linked to the created ``betrokkene``

    2. User is authenticated, but unknow in the API:

      * create ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the created ``partij``
      * create ``gigitaalAdres`` records linked to the created ``betrokkene``. If the address is
        submitted as "isNewPreferred", then it's also linked to the created ``partij``

    3. User is authenticated, known in the API and uses pre-filled data:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``

    4. User is authenticated, known in the API and submits new addresses:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * create ``gigitaalAdres`` records linked to the created ``betrokkene`` for the new addresses.
        If the address is submitted as "isNewPreferred", then it's also linked to the ``partij``
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

    plugin = prefill_registry[prefill_form_variable.prefill_plugin]
    options_serializer = plugin.options(data=prefill_form_variable.prefill_options)
    options_serializer.is_valid(raise_exception=True)
    plugin_options = options_serializer.validated_data
    api_group = plugin_options["customer_interactions_api_group"]

    channels_to_address_types = {v: k for k, v in ADDRESS_TYPES_TO_CHANNELS.items()}

    with get_customer_interactions_client(api_group) as client:
        if not submission.is_authenticated:
            # 1. User is not authenticated
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

        return None  # todo replace with logic described in the docstring
