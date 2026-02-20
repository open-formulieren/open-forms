from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import wraps

from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.formio.typing import Component
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.typing import StrOrPromise

from ...base import (
    AppointmentDetails,
    BasePlugin,
    CustomerDetails,
    Location,
    Product,
    RequiredGroupFields,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ...registry import register
from ...utils import create_base64_qrcode
from .client import JccRestClient, NoServiceConfigured
from .constants import CustomerFields, FieldState, GenderType, get_component
from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig
from .types import (
    AppointmentData,
    CustomerFields as RawCustomerFields,
    Location as RawLocation,
)

logger = structlog.stdlib.get_logger(__name__)

# pair of key/identifier + human readable label
type FieldLabelPair = tuple[str, StrOrPromise]


@dataclass
class RequireOneOfRule:
    enabled: bool
    field_label_pairs: Sequence[FieldLabelPair]

    @property
    def fields(self) -> Sequence[str]:
        return [field for field, _ in self.field_label_pairs]

    @property
    def labels(self) -> Sequence[StrOrPromise]:
        return [label for _, label in self.field_label_pairs]


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
        self, current_products: list[Product] | None = None, location_id: str = ""
    ) -> list[Product]:
        with JccRestClient() as client:
            if current_products is None:
                data = client.get_activity_list_for_appointment(location_id)
            else:
                data = client.get_additional_activity_list_for_appointment(
                    [product.identifier for product in current_products], location_id
                )

        products = [
            Product(
                identifier=product["id"],
                name=product.get("description", ""),
                description=product.get("necessities", ""),
            )
            for product in data
        ]

        return products

    @staticmethod
    def _create_location(location: RawLocation) -> Location:
        """Create a Location object from the API response data."""
        address = location.get("address", {})

        # Note: the schema defines a string or None (which could also mean the field is
        # missing), but all the examples from the test data include an empty string
        # instead of None, so we include it in the checks
        if (street_name := address.get("streetName")) in (None, ""):
            formatted_address = ""
        elif (house_number := address.get("houseNumber")) in (None, ""):
            formatted_address = street_name
        elif (suffix := address.get("houseNumberSuffix")) in (None, ""):
            formatted_address = f"{street_name} {house_number}"
        else:
            formatted_address = f"{street_name} {house_number}{suffix}"

        return Location(
            identifier=location["id"],
            name=location.get("description") or "",
            address=formatted_address,
            city=address.get("city") or "",
            postalcode=address.get("postalCode") or "",
        )

    @with_graceful_default(default=[])
    def get_locations(self, products: list[Product] | None = None) -> list[Location]:
        with JccRestClient() as client:
            if products is None:
                data = client.get_location_list()
            else:
                data = client.get_location_list_for_appointment(
                    [product.identifier for product in products]
                )

        locations = [self._create_location(location) for location in data]

        return locations

    @with_graceful_default(default=[])
    def get_dates(
        self,
        products: list[Product],
        location: Location,
        start_at: date | None = None,
        end_at: date | None = None,
    ) -> list[date]:
        with JccRestClient() as client:
            min_date, max_date = client.get_appointment_date_range_for_activities(
                [product.identifier for product in products]
            )
            start_at = max(start_at, min_date) if start_at else min_date
            # There is a limit of 50 days when requesting the available dates/times
            end_at = min(end_at or max_date, start_at + timedelta(days=50))

            # Ensure there is at least one day between the start and end date. The
            # endpoint returns no available dates if they are the same.
            end_at = start_at + timedelta(days=1) if end_at == start_at else end_at

            data = client.get_available_times_for_appointment(
                location.identifier,
                start_at,
                end_at,
                [(product.identifier, product.amount) for product in products],
            )
        return [datetime_.date() for datetime_ in data]

    @with_graceful_default(default=[])
    def get_times(
        self,
        products: list[Product],
        location: Location,
        day: date,
    ) -> list[datetime]:
        with JccRestClient() as client:
            # We only care about the times of this specific day, so set the `to_date`
            # argument to the next day.
            return list(
                client.get_available_times_for_appointment(
                    location.identifier,
                    day,
                    day + timedelta(days=1),
                    [(product.identifier, product.amount) for product in products],
                )
            )

    def _get_default_component(
        self,
        condition: bool | None,
        *field_values: FieldState | None,
        component_factory,
    ) -> list[Component]:
        """
        Returns a list with the default component when isAnyPhoneNumberRequired or
        areFirstNameOrInitialsRequired are set to True.
        """
        if condition and all(v == FieldState.hidden for v in field_values):
            return [component_factory]

        return []

    def _extract_rendered_fields(
        self, required_fields: RawCustomerFields
    ) -> dict[str, bool]:
        """
        Based on the retrieved fields returns a dict with the field names and a boolean,
        set according to whether they are required or not.
        """
        excluded_fields = {
            CustomerFields.last_name,
            CustomerFields.phone_number,
        }

        # according to JCC, missing fields are considered to be visible, so we check which
        # fields are missing from the response (except lastName and phone number which
        # are treated a bit differently) and we add them as optional
        fields: dict[str, bool] = {
            possible_field: False
            for possible_field in CustomerFields.values
            if possible_field not in required_fields
            and possible_field not in excluded_fields
        }

        # JCC has different names for the main phone number in the `customer/customerfields/required`
        # and the POST `appointment` endpoints, so we use `mainPhoneNumber` to find
        # it in the response of the required fields (in our constans file we have the name
        # that the appointment create body needs)
        if "mainPhoneNumber" not in required_fields:
            fields.setdefault("mainPhoneNumber", False)

        # update the fields with the required ones
        # these fields are present in the response and they can only be hidden or required,
        # so we keep only the required ones
        fields.update(
            **{
                field: True
                for field, state in required_fields.items()
                if state == FieldState.required
            }
        )

        # race condition in case we require a field but none of them is present
        def ensure_one_is_present(flag: str, field_a: str, field_b: str) -> None:
            if not required_fields.get(flag):
                return

            if field_a in fields and field_b not in fields:
                fields[field_a] = True
            elif field_b in fields and field_a not in fields:
                fields[field_b] = True

        ensure_one_is_present(
            "areFirstNameOrInitialsRequired",
            "firstName",
            "initials",
        )

        ensure_one_is_present(
            "isAnyPhoneNumberRequired",
            "mainPhoneNumber",
            "mobilePhoneNumber",
        )

        return fields

    @with_graceful_default(default=tuple([]))
    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> tuple[list[Component], list[RequiredGroupFields] | None]:
        product_ids = [product.identifier for product in products]
        with JccRestClient() as client:
            # Each field from the API has a value which determines if it's visible, hidden
            # or required. We need only the visible (optional fields in the form) and the
            # required ones (required fields in the form). See FieldState in constants
            required_fields = client.get_required_customer_fields(product_ids)

        # If 'areFirstNameOrInitialsRequired' and 'isAnyPhoneNumberRequired' are set
        # to 'true' in the configuration and both fields are set to 'required' by the
        # municipality, then both must still be completed. The municipality can specify
        # in the application whether a field should only be 'visible' or whether a
        # field should be 'required.'
        GROUP_RULES = [
            RequireOneOfRule(
                enabled=required_fields.get("isAnyPhoneNumberRequired"),
                field_label_pairs=(
                    ("phoneNumber", CustomerFields.phone_number.label),
                    ("mobilePhoneNumber", CustomerFields.mobile_phone_number.label),
                ),
            ),
            RequireOneOfRule(
                enabled=required_fields.get("areFirstNameOrInitialsRequired"),
                field_label_pairs=(
                    ("firstName", CustomerFields.first_name.label),
                    ("initials", CustomerFields.initials.label),
                ),
            ),
        ]

        # optional (only visible) and required customer fields
        rendered_fields = self._extract_rendered_fields(required_fields)

        components = []
        # Name / initials defaults
        components.extend(
            self._get_default_component(
                required_fields.get("areFirstNameOrInitialsRequired"),
                required_fields.get("initials"),
                required_fields.get("firstName"),
                component_factory=get_component(CustomerFields.first_name, True),
            )
        )

        # Last name is always required
        components.append(get_component(CustomerFields.last_name, True))

        # Phone defaults
        components.extend(
            self._get_default_component(
                required_fields.get("isAnyPhoneNumberRequired"),
                required_fields.get("mainPhoneNumber"),
                required_fields.get("mobilePhoneNumber"),
                component_factory=get_component(CustomerFields.phone_number, True),
            )
        )
        # JCC has different names for the main phone number in the `customer/customerfields/required`
        # and the POST `appointment` endpoints, so we use `mainPhoneNumber` to find
        # it in the response of the required fields but we send `phoneNumber` when we
        # create the body for the appointment
        if "mainPhoneNumber" in rendered_fields:
            rendered_fields["phoneNumber"] = rendered_fields.pop("mainPhoneNumber")

        # Explicitly declared visible fields
        for field, is_required in rendered_fields.items():
            components.append(get_component(CustomerFields(field), is_required))

        rendered_keys = {component["key"] for component in components}
        required_group_fields = []

        for rule in GROUP_RULES:
            if not rule.enabled:
                continue

            active_fields = [field for field in rule.fields if field in rendered_keys]

            if len(active_fields) < 2:
                continue

            # Do not apply require_one_of if all fields are already required
            if all(rendered_fields.get(field) for field in active_fields):
                continue

            active_labels = [
                str(label)
                for field, label in rule.field_label_pairs
                if field in rendered_keys
            ]

            description = _(
                "At least one of the following fields must be filled in: {fields}"
            ).format(fields=", ".join(active_labels))

            for component in components:
                if component["key"] in active_fields:
                    component["description"] = description

            required_group_fields.append(
                {
                    "type": "require_one_of",
                    "fields": tuple(active_fields),
                    "error_message": _(
                        "At least one of the following fields is required: {fields}."
                    ).format(fields=", ".join(active_labels)),
                }
            )

        return components, required_group_fields or None

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: CustomerDetails[CustomerFields],
        remarks: str = "",
    ) -> str:
        with JccRestClient() as jcc_client:
            activities = [(product.identifier, product.amount) for product in products]

            # We have to use an extra endpoint to find the duration (in minutes) for an
            # appointment
            appointment_duration = jcc_client.get_duration_for_appointment(
                start_at.date(), activities
            )

            appointment_data: AppointmentData = {
                "id": None,  # id (as null) is required by JCC even for a new appointment
                "activityList": [
                    {"activityId": id_, "amount": amount} for id_, amount in activities
                ],
                "customerList": [
                    # We send a default to 0 (other) gender because it's a required field in JCC
                    # (0=other, 1=male, 2=female)
                    {
                        "gender": GenderType.other.value,
                        **client.details,
                        "id": None,
                        "isMainCustomer": True,
                    },
                ],
                "fromDateTime": start_at.isoformat(),
                "toDateTime": (
                    start_at + timedelta(minutes=appointment_duration)
                ).isoformat(),
                "locationId": location.identifier,
                "message": remarks,
                "fieldList": None,
            }

            result = jcc_client.add_appointment(appointment_data)

            if result.get("acknowledgeIsSuccess"):
                return result["id"]

            error = AppointmentCreateFailed(
                f"Could not create appointment, got code={result['code']}"
            )

            logger.error(
                "appointment_create_failure",
                products=activities,
                location=location,
                start_at=start_at,
                code=result["code"],
                message=result.get("message"),
                exc_info=error,
            )

            raise error

    def delete_appointment(self, identifier: str) -> None:
        with JccRestClient() as client:
            result = client.cancel_appointment(identifier)

            # JCC is supposed to return a boolean `acknowledgeIsSuccess` (required field
            # according to the specification) in the successful response. This is not the
            # case in the test instance so asserting the id is the next logical "required"
            # field
            if not result.get("id"):
                error = AppointmentDeleteFailed(
                    f"Could not delete appointment, got code={result['code']}"
                )

                logger.error(
                    "appointment_delete_failure",
                    appointment_identifier=identifier,
                    code=result["code"],
                    message=result.get("message"),
                    exc_info=error,
                )

                raise error

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

            location = self._create_location(location_details)

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
                location=location,
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
        try:
            client = JccRestClient()
        except NoServiceConfigured as exc:
            raise InvalidPluginConfiguration(
                _("No JCC REST service configured.")
            ) from exc

        with client:
            try:
                client.get_version()
            except JccRestException as exc:
                raise InvalidPluginConfiguration(
                    _("Invalid plugin configuration: {exc}").format(exc=exc)
                )

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
