from collections.abc import Callable
from datetime import date, datetime, timedelta
from functools import wraps

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.formio.typing import Component
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...registry import register
from .client import JccRestClient, Location as RawLocation, NoServiceConfigured
from .constants import CustomerFields
from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)


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
                [product.identifier for product in products],
                [product.amount for product in products],
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
                    [product.identifier for product in products],
                    [product.amount for product in products],
                )
            )

    @with_graceful_default(default=[])
    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> list[Component]:
        return []

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
