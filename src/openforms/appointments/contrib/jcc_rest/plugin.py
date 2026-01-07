from collections.abc import Callable
from datetime import date, datetime, timedelta
from functools import wraps

from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from openforms.formio.typing import Component

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...exceptions import (
    AppointmentException,
)
from ...registry import register
from ...utils import create_base64_qrcode
from .client import JccRestClient
from .constants import CustomerFields, get_component
from .exceptions import GracefulJccRestException
from .models import JccRestConfig


def with_graceful_default[T, **P](
    default: T,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except GracefulJccRestException:
                return default

        return wrapper

    return decorator


@register("jcc_rest")
class JccRestPlugin(BasePlugin):
    """
    Plugin for JCC-Afspraken using RESTful API

    Website: https://jccsoftware.nl/
    API Specification:  https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
    """

    verbose_name = _("JCC Rest")
    supports_multiple_products = True

    @with_graceful_default(default=[])
    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        return []

    def _get_all_locations(self, client) -> list[Location]:
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
        product_ids = [product.identifier for product in products]
        with JccRestClient() as client:
            # Each field from the API has a value which determines if it's visible, hidden
            # or required. We need only the visible (optional fields in the form) and the
            # required ones (required fields in the form).
            # 0 = visible
            # 1 = hidden
            # 2 = required
            required_fields = client.get_required_customer_fields(product_ids)

            # If 'areFirstNameOrInitialsRequired' and 'isAnyPhoneNumberRequired' are set
            # to 'true' in the configuration and both fields are set to 'required' by the
            # municipality, then both must still be completed. The municipality can specify
            # in the application whether a field should only be 'visible' or whether a
            # field should be 'required.'
            default_number_field = []
            default_name_or_initials = []
            if required_fields.get("isAnyPhoneNumberRequired"):
                main_number = required_fields.get("mainPhoneNumber")
                mobile_number = required_fields.get("mobilePhoneNumber")
                if (not main_number or main_number == 1) and (
                    not mobile_number or mobile_number == 1
                ):
                    default_number_field = [
                        get_component(CustomerFields.phone_number, True)
                    ]
            if required_fields.get("areFirstNameOrInitialsRequired"):
                initials = required_fields.get("initials")
                first_name = required_fields.get("firstName")
                if (not initials or initials == 1) and (
                    not first_name or first_name == 1
                ):
                    default_name_or_initials = [
                        get_component(CustomerFields.first_name, True)
                    ]

            field_names = {
                field: value == 2
                for field, value in required_fields.items()
                if value in (0, 2)
            }

            # last name is always required by JCC
            last_name = [get_component(CustomerFields.last_name, True)]

            # JCC has different names for the main phone number in the `customer/customerfields/required`
            # and the POST `appointment` endpoints, so we use `mainPhoneNumber` to find
            # it in the response of the required fields but we send `phoneNumber` when we
            # create the body for the appointment
            main_phone_number = []
            if "mainPhoneNumber" in field_names:
                main_phone_number = [
                    get_component(
                        CustomerFields.phone_number, field_names["mainPhoneNumber"]
                    )
                ]
                field_names.pop("mainPhoneNumber", None)

            return (
                default_number_field
                + default_name_or_initials
                + last_name
                + main_phone_number
                + [
                    get_component(CustomerFields(field), required)
                    for field, required in field_names.items()
                ]
            )

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: CustomerDetails[CustomerFields],
        remarks: str = "",
    ) -> str:
        with JccRestClient() as jcc_client:
            product_ids: list[str] = []
            product_amounts: list[int] = []
            for product in products:
                product_ids.append(product.identifier)
                product_amounts.append(product.amount)

            # We have to use an extra endpoint to find the duration (in minutes) for an
            # appointment
            appointment_duration = jcc_client.get_duration_for_appointment(
                start_at.date(), product_ids, product_amounts
            )

            appointment_data = {
                "id": None,  # id (as null) is required by JCC even for a new appointment
                "activityList": [
                    {"activityId": id_, "amount": amount}
                    for id_, amount in zip(product_ids, product_amounts, strict=False)
                ],
                "customerList": [
                    {**client.details, "id": None, "isMainCustomer": True},
                ],
                "fromDateTime": start_at.isoformat(),
                "toDateTime": (
                    start_at + timedelta(minutes=appointment_duration)
                ).isoformat(),
                "locationId": location.identifier,
                "message": remarks,
                "fieldList": None,
            }

            # We send a default to 0 (None) gender because it's a required field in JCC
            # (0=none, 1=male, 2=female)
            if "gender" not in client.details:
                appointment_data["customerList"][0]["gender"] = 0

            result = jcc_client.add_appointment(appointment_data)

            assert result is not None and result.get("acknowledgeIsSuccess") is True

            return result.get("id")

    def delete_appointment(self, identifier: str) -> None:
        with JccRestClient() as client:
            client.cancel_appointment(identifier)

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        with JccRestClient() as client:
            appointment_details = client.get_appointment(identifier)
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
            # Do another request to retrieve all the extra information.
            location_id = appointment_details.get("location", {}).get("id")
            location_details = client.get_location(location_id)

            address = location_details.get("address", {})

            if (street_name := address.get("streetName")) in (None, ""):
                formatted_address = ""
            elif (house_number := address.get("houseNumber")) in (None, ""):
                formatted_address = street_name
            elif (suffix := address.get("houseNumberSuffix")) in (None, ""):
                formatted_address = f"{street_name} {house_number}"
            else:
                formatted_address = f"{street_name} {house_number}{suffix}"

            qrcode = client.get_appointment_qr_code(identifier)
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
                    city=address.get("city") or "",
                    postalcode=address.get("postalCode") or "",
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
