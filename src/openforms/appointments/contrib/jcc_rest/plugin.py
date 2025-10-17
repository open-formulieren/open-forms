from collections.abc import Callable
from datetime import date, datetime
from functools import wraps
from typing import ParamSpec, TypeVar

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.formio.typing import Component

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...registry import register
from ...utils import get_formatted_phone_number
from .client import JccRestClient
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
        product_ids = squash_ids(products)

        with JccRestClient() as client:
            # TODO
            # each field from the API has a value which determines if it's required or not
            # Make sure we know the exact purpose and usage of 0,1 and 2

            # 0 = visible
            # 1 = hidden
            # 2 = required

            required_fields = client.list_customer_required_fields(product_ids)

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
            + [FIELD_TO_FORMIO_COMPONENT[field] for field in field_names]
        )

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: CustomerDetails[CustomerFields],
        remarks: str = "",
    ) -> str:
        return ""

    def delete_appointment(self, identifier: str) -> None:
        return None

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        # TODO
        # Fix the wrong return and remove the comment
        return None  # type: ignore [reportIncompatibleMethodOverride]

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
