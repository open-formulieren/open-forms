from collections.abc import Callable
from datetime import date, datetime, timedelta
from functools import wraps
from typing import ParamSpec, TypeVar

from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import structlog
from requests.exceptions import RequestException

from openforms.formio.typing import Component

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ...registry import register
from ...utils import create_base64_qrcode, get_formatted_phone_number
from .client import Client, JccRestClient
from .constants import FIELD_TO_FORMIO_COMPONENT, CustomerFields
from .exceptions import GracefulJccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)

Param = ParamSpec("Param")
T = TypeVar("T")
FuncT = Callable[Param, T]


def squash_ids(products: list[Product]):
    # When more of the same product are required (amount > 1), the ID needs to be repeated.
    return sum(([product.identifier] * product.amount for product in products), [])


def with_graceful_default(default: T):
    def decorator(func: FuncT) -> FuncT:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except GracefulJccRestException:
                return default

        return wrapper

    return decorator


# TODO
# Handle exceptions and add proper logs for the `JccRestPlugin` methods as soon as we have
# all the answers from JCC.


@register("jcc_rest")
class JccRestPlugin(BasePlugin):
    """
    Plugin for JCC-Afspraken using RESTful API

    Website: https://jccsoftware.nl/
    API Specification:  https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
    """

    verbose_name = _("JCC Rest")
    supports_multiple_products = True
    normalizers = {
        CustomerFields.phone_number: [get_formatted_phone_number],
        CustomerFields.mobile_phone_number: [get_formatted_phone_number],
    }

    @with_graceful_default(default=[])
    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        return []

    def _get_all_locations(self, client: Client) -> list[Location]:
        # TODO
        # Fix the argument's type (client), should be an instance of the Client class
        return []

    @with_graceful_default(default=[])
    def get_locations(
        self,
        products: list[Product] | None = None,
    ) -> list[Location]:
        if products is None:
            # call the internal method `_get_all_locations` for retrieving the whole list
            pass

        return []

    @with_graceful_default(default=[])
    def get_dates(
        self,
        products: list[Product],
        location: Location,
        start_at: date | None = None,
        end_at: date | None = None,
    ) -> list[date]:
        return []

    @with_graceful_default(default=[])
    def get_times(
        self,
        products: list[Product],
        location: Location,
        day: date,
    ) -> list[datetime]:
        return []

    @with_graceful_default(default=[])
    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> list[Component]:
        product_ids = squash_ids(products)

        with JccRestClient() as client:
            # each field from the API has a value which determines if it's required or not
            # 0 = visible
            # 1 = hidden
            # 2 = required

            required_fields = client.list_customer_required_fields(product_ids)

            # TODO
            # See if these checks are really needed (after the JCC's answer)

            default_number_field = []
            default_name_or_initials = []
            if required_fields.get("isAnyPhoneNumberRequired"):
                has_any_number_field = any(
                    required_fields.get(number_field) == 2
                    for number_field in ("mainPhoneNumber", "mobilePhoneNumber")
                )

                # fallback to main phone number
                if not has_any_number_field:
                    default_number_field = [
                        FIELD_TO_FORMIO_COMPONENT[CustomerFields.phone_number]
                    ]

            if required_fields.get("areFirstNameOrInitialsRequired"):
                has_name_or_initials_field = any(
                    required_fields.get(given_field) == 2
                    for given_field in ("firstName", "initials")
                )

                # fallback to first name
                if not has_name_or_initials_field:
                    default_name_or_initials = [
                        FIELD_TO_FORMIO_COMPONENT[CustomerFields.first_name]
                    ]

            field_names = [
                field for field, value in required_fields.items() if value == 2
            ]

        last_name = [FIELD_TO_FORMIO_COMPONENT[CustomerFields.last_name]]
        return (
            default_number_field
            + default_name_or_initials
            + last_name
            + [getattr(FIELD_TO_FORMIO_COMPONENT, field) for field in field_names]
        )

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: CustomerDetails[CustomerFields],
        remarks: str = "",
    ) -> str:
        appointment_data = {
            "activityList": [
                {"activityId": product.identifier} for product in products
            ],
            "customerList": [
                {key: value for key, value in client.details.items()},
            ],
            "fromDateTime": start_at.isoformat(),
            # TODO
            # Should we take into account the activity's appointmentDuration or the
            # endpoint in appointments for this?
            "toDateTime": (start_at + timedelta(minutes=35)).isoformat(),
            "locationId": location.identifier,
            "message": remarks,
        }

        with JccRestClient() as jcc_client:
            try:
                result = jcc_client.book_appointment(appointment_data)

                # TODO
                # The response contains the `acknowledgeIsSuccess` key which we have
                # to make sure is the one we can trust.
                if result.get("acknowledgeIsSuccess"):
                    return result["id"]

                # In case of status: 200 we have the property `validateErrors` in the
                # response
                errors = result.get("validateErrors")

                error = AppointmentCreateFailed(
                    f"Could not create appointment, got errors={errors}"
                )

                logger.error(
                    "appointment_create_failure",
                    products=products,
                    location=location,
                    start_at=start_at,
                    errors=errors,
                    exc_info=error,
                )
                raise error
            except RequestException as e:
                if (response := e.response) is not None:
                    data = response.json()

                    # In case of status: 400,403,500 we do not get `validateErrors` in
                    # response, instead we get `errors`
                    errors = data.get("errors", [])
                    raise AppointmentCreateFailed(
                        f"Could not create appointment, got errors={errors}"
                    )

                raise AppointmentCreateFailed("Could not create appointment")

    def delete_appointment(self, identifier: str) -> None:
        with JccRestClient() as client:
            try:
                result = client.cancel_appointment(identifier)

                # TODO
                # The response contains the `acknowledgeIsSuccess` key which we have
                # to make sure is the one we can trust.
                if not result.get("acknowledgeIsSuccess"):
                    # In case of status: 200 we have the property `validateErrors` in the
                    # response
                    errors = result.get("validateErrors")

                    error = AppointmentCreateFailed(
                        f"Could not cancel appointment, got errors={errors}"
                    )

                    logger.error(
                        "appointment_cancel_failure",
                        appointment_identifier=identifier,
                        exc_info=error,
                    )
                    raise error
            except RequestException as e:
                if (response := e.response) is not None:
                    data = response.json()

                    # In case of status: 400,403,500 we do not get `validateErrors` in
                    # response, instead we get `errors`
                    errors = data.get("errors", [])
                raise AppointmentDeleteFailed(
                    f"Could not cancel appointment, got errors={errors}"
                )

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        with JccRestClient() as client:
            appointment_details = client.retrieve_appointment_details(identifier)
            if not appointment_details:
                raise AppointmentException("No appointment details could be retrieved.")

            products = [
                Product(
                    identifier=product.get("activity", {}).get("id"),
                    name=product.get("activity", {}).get("description"),
                    amount=product.get("amount"),
                )
                for product in appointment_details.get("activityList", {})
            ]

            # The details of the appointment only have the id and the description available.
            # Do another request to retrieve all the extra information needed.
            location_id = appointment_details.get("location", {}).get("id")
            location_details = client.retrieve_location_details(location_id)

            address = location_details.get("address", {})

            if (street_name := address.get("streetName")) in (None, ""):
                formatted_address = None
            elif (house_number := address.get("houseNumber")) in (None, ""):
                formatted_address = street_name
            elif (suffix := address.get("houseNumberSuffix")) in (None, ""):
                formatted_address = f"{street_name} {house_number}"
            else:
                formatted_address = f"{street_name} {house_number}{suffix}"

            qrcode = client.retrieve_appointment_qr_code(identifier)
            qrcode_base64 = create_base64_qrcode(qrcode)
            qr_label = _("QR-code")
            qr_value = format_html(
                '<img src="data:image/png;base64,{qrcode_base64}" alt="{qrcode}" />',
                qrcode_base64=qrcode_base64,
                qrcode=qrcode,
            )

            result = AppointmentDetails(
                identifier=identifier,
                products=products,
                location=Location(
                    identifier=location_details["id"],
                    name=location_details.get("description") or "",
                    address=formatted_address,
                    city=address.get("city"),
                    postalcode=address.get("postalCode"),
                ),
                start_at=datetime.fromisoformat(
                    appointment_details.get("startDateTime", "")
                ),
                end_at=datetime.fromisoformat(
                    appointment_details.get("endDateTime", "")
                ),
                remarks=appointment_details.get("message"),
                other={qr_label: qr_value},
            )

            return result

    def check_config(self) -> None:
        pass

    def get_config_actions(self) -> list[tuple]:
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:jcc_rest_jccrestconfig_change",
                    args=(JccRestConfig.singleton_instance_id,),
                ),
            ),
        ]
