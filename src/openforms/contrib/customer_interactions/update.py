import warnings
from collections.abc import Mapping
from typing import TypedDict

from django.conf import settings

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
from openforms.prefill.contrib.customer_interactions.variables import (
    fetch_user_variable_from_profile_component,
)
from openforms.prefill.registry import register as prefill_registry
from openforms.submissions.models import EmailVerification, Submission

from .client import CustomerInteractionsClient, get_customer_interactions_client
from .constants import (
    ADDRESS_TYPES_TO_CHANNELS,
    USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG,
)
from .typing import CommunicationChannel

logger = structlog.stdlib.get_logger(__name__)


class EmailNotVerifiedException(Exception):
    pass


class DigitalAddressResults(TypedDict):
    created: list[DigitaalAdres]
    updated: list[DigitaalAdres]


class UpdateCustomerInteractionsResult(TypedDict):
    klantcontact: KlantContact
    betrokkene: Betrokkene
    onderwerpobject: OnderwerpObject
    digital_addresses: DigitalAddressResults
    partij_uuid: str


# TODO
# This is a workaround needed because Open Klant does not support these checks regarding
# the referentie. This has an expiry date (upper bound: Open Forms 5.0).
def clear_existing_standard_address_reference(
    client: CustomerInteractionsClient,
    party_uuid: str,
    reference: str,
    channel: SoortDigitaalAdres,
) -> DigitaalAdres | None:
    """
    Update the address regarding the `referentie` attribute.

    Open Klant has a unique constraint regarding the fields ``partij``, ``referentie``,
    ``soort_digitaal_adres`` (combined). This means that each time we need to add a new
    preferred address with ``CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS="referentie"``
    we have to make sure any existing address with the same referentie (portaalvoorkeur)
    is updated.
    """
    if reference != USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG:
        return

    if existing_address_with_reference := client.get_unique_digital_address(
        party_uuid,
        channel,
        reference,
    ):
        warnings.warn(
            "Using reference as isStandaardAdres alternative will be removed in Open Forms 5.0",
            DeprecationWarning,
            stacklevel=2,
        )
        updated_existing_address = client.update_digital_address_for_party(
            address=existing_address_with_reference["adres"],
            party_uuid=party_uuid,
            is_preferred=False,
            reference="",
            address_uuid=existing_address_with_reference["uuid"],
        )
        if updated_existing_address:
            assert updated_existing_address["referentie"] == ""

        return updated_existing_address


def update_customer_interaction_data(
    submission: Submission, profile_key: str
) -> UpdateCustomerInteractionsResult | None:
    """
    Writes to the Customer interaction API when the form with profile component is submitted.

    There are several flows how the information is updated depending on if the user and
    their digital addresses are known in the Customer Interactions API

    1. User is not authenticated:

      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject``
      * create ``digitaalAdres`` records linked to the created ``betrokkene``

    2. User is authenticated, but unknown in the API:

      * create ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the created ``partij``
      * create ``digitaalAdres`` records linked to the created ``betrokkene``. If the address is
        submitted as ``isNewPreferred``, then it's also linked to the created ``partij``.
        We also update it either with ``isStandaardAdres`` = True or
        ``referentie ==  USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG``,
        based on the setting ``CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS``, never
        both at the same time.

    3. User is authenticated, known in the API and uses pre-filled data:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * create ``digitaalAdres`` records linked to the created ``betrokkene`` if the used address is not default

    4. User is authenticated, known in the API and submits new addresses:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * create ``digitaalAdres`` records linked to the created ``betrokkene`` for the new addresses.
        If the address is submitted as ``isNewPreferred`` or is verified via Open Forms email
        verification flow, then it's also linked to the ``partij``. We also update it with
        ``isStandaardAdres`` = True or ``referentie ==  USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG``,
        based on the env variable ``CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS``

    5. User is authenticated, known in the API and submits existing addresses with the changed preference:

      * find ``partij`` for the user
      * create ``contactMoment``, ``betrokkene`` and ``onderwerpObject`` and link ``betrokkene``
        to the found ``partij``
      * if the address is submitted as ``useOnlyOnce``, then we don't update it
      * if the address is submitted as ``isNewPreferred``, and the existing address is not
        preferred (``isStandaardAdres`` == False or ``referentie`` == "") then we update
        it with ``isStandaardAdres`` = True or
        ``referentie ==  USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG``, based on the env variable
        ``CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS``

    """
    # check if `referentie` or `isStandaardAdres` needs to be used for preferred address,
    # isStandaardAdres is the default one
    should_use_reference_for_standard_address = (
        settings.CUSTOMER_INTERACTIONS_USE_REFERENCE_FOR_STANDARD_ADDRESS
    )
    open_forms_reference = submission.public_registration_reference

    # submission profile data
    state = submission.variables_state
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
            party, _ = client.get_or_create_party(auth_attribute, auth_value)
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
            if not address_value:
                continue

            address_channel: SupportedChannels = digital_address["type"]
            is_address_new_preferred = (
                digital_address.get("preferenceUpdate") == "isNewPreferred"
            )

            # prefill values
            prefill_communication_channel: CommunicationChannel | None = next(
                (value for value in prefill_value if value["type"] == address_channel),
                None,
            )

            if not prefill_communication_channel:
                prefill_channel_options = []
            else:
                prefill_channel_options = [
                    option["address"]
                    for option in prefill_communication_channel["options"]
                ]

            prefill_preferred = (
                prefill_communication_channel["preferred"]
                if prefill_communication_channel
                else None
            )
            is_preferred_address: bool = bool(address_value == prefill_preferred)

            # address verification is only supported for email addresses. Check if the email
            # address is already verified in Open Klant (we already have the prefill data),
            # otherwise grab the verification date from our db (the verification has been
            # done by Open Forms).
            is_already_verified = False
            verification_date = None

            if address_channel == "email":
                if prefill_value and prefill_communication_channel:
                    is_already_verified = any(
                        option["address"] == address_value
                        and option["verification_date"]
                        for option in prefill_communication_channel["options"]
                    )

                if not is_already_verified:
                    verification = (
                        EmailVerification.objects.filter(
                            submission=submission,
                            component_key=profile_key,
                            email=address_value,
                            verified_on__isnull=False,
                        )
                        .order_by("-verified_on")
                        .first()
                    )

                    if not verification:
                        logger.warning(
                            "email_unverified",
                            component=profile_key,
                            submission_uuid=str(submission.uuid),
                        )
                        raise EmailNotVerifiedException()

                    verification_date = verification.verified_on.date().isoformat()

            # if address is already a default for phone numbers or already the default
            # and verified in Open Klant - we don't create/update digital addresses
            if (is_preferred_address and address_channel == "phoneNumber") or (
                is_preferred_address
                and address_channel == "email"
                and is_already_verified
            ):
                continue

            reference = (
                USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG
                if should_use_reference_for_standard_address
                and is_address_new_preferred
                else open_forms_reference
            )

            if address_value in prefill_channel_options:
                # flow 5. we update it only if it's marked as "isNewPreferred" or it's now
                # verified via Open Forms
                if verification_date or is_address_new_preferred:
                    # check for possible duplicate addresses
                    updated_existing_address = (
                        clear_existing_standard_address_reference(
                            client,
                            party_uuid,
                            reference,
                            channels_to_address_types[address_channel],
                        )
                    )
                    if updated_existing_address:
                        updated_addresses.append(updated_existing_address)

                    # now it's safe to update the address
                    updated_address = client.update_digital_address_for_party(
                        address=address_value,
                        party_uuid=party_uuid,
                        is_preferred=(
                            None
                            if should_use_reference_for_standard_address
                            and reference == USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG
                            else is_address_new_preferred
                        ),
                        verification_date=verification_date
                        if not is_already_verified
                        else None,
                        reference=reference,
                    )
                    if updated_address:
                        updated_addresses.append(updated_address)

                # flow 3. we create a new address and link it to betrokkene
                else:
                    created_address = client.create_digital_address(
                        address=address_value,
                        address_type=channels_to_address_types[address_channel],
                        betrokkene_uuid=customer_contact["betrokkene"]["uuid"],
                        is_preferred=False,
                        verification_date=(
                            verification_date if not is_already_verified else None
                        ),
                        reference=open_forms_reference,
                    )
                    created_addresses.append(created_address)
            else:
                # flows 1,2 4: we create a new address and link it to betrokkene
                # flows 2,4: we link a new address to partij if it's marked as "isNewPreferred"

                # check for possible duplicate addresses
                updated_existing_address = clear_existing_standard_address_reference(
                    client,
                    party_uuid,
                    reference,
                    channels_to_address_types[address_channel],
                )
                if updated_existing_address:
                    updated_addresses.append(updated_existing_address)

                # now it's safe to create the address
                created_address = client.create_digital_address(
                    address=address_value,
                    address_type=channels_to_address_types[address_channel],
                    betrokkene_uuid=customer_contact["betrokkene"]["uuid"],
                    party_uuid=party_uuid if is_address_new_preferred else "",
                    is_preferred=(
                        False
                        if should_use_reference_for_standard_address
                        and reference == USE_REFERENCE_FOR_STANDARD_ADDRESS_FLAG
                        else is_address_new_preferred
                    ),
                    verification_date=(
                        verification_date if not is_already_verified else None
                    ),
                    reference=reference,
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
