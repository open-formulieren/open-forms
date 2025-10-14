from collections.abc import Callable
from contextlib import contextmanager
from datetime import date, datetime
from functools import cached_property, wraps
from typing import ParamSpec, TypeVar

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog

from openforms.formio.typing import Component

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...registry import register
from .constants import CustomerFields
from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)

Param = ParamSpec("Param")
T = TypeVar("T")
FuncT = Callable[Param, T]


# TODO-5696: we might be able to include the error message from the response
@contextmanager
def log_api_errors(event: str):
    try:
        yield
    except requests.RequestException as exc:
        logger.exception(event, exc_info=exc)
        raise GracefulJccRestException("JCC REST API call failed") from exc
    except Exception as exc:
        raise JccRestException from exc


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


class Client:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def get(self, url, params=None):
        return requests.get(
            f"{self.base_url}{url}", headers=self.headers, params=params
        )


@register("jcc_rest")
class JccRestPlugin(BasePlugin):
    """
    Plugin for JCC-Afspraken using RESTful API

    Website: https://jccsoftware.nl/
    API Specification:  https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
    """

    verbose_name = _("JCC Rest")
    supports_multiple_products = True

    """
    Get a new token with:

    response = requests.post(
        f"{base}connect/token",
        data={"grant_type": "client_credentials", "scope": "warp-api"},
        auth=(client_id, secret)
    )
    """

    @cached_property
    def client(self):
        return Client(
            "https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/",
            headers={
                "Authorization": (

                ),
                "Accept": "application/json",
                "language": "nl",
            },
        )

    @with_graceful_default(default=[])
    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        return []

    @staticmethod
    def _create_location(location) -> Location:
        """
        Create a location from the API response data.

        TODO-5696: would it make sense to type hint the location?

        Source: https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html#tag/WARPLocation/paths/~1api~1warp~1v1~1location~1%7Bid%7D/get

        Note: except for "id", all properties are listed in the API spec as
        "[type] or null"
        """
        address = location.get("address", {})

        # Note: the schema defines a string or None, but all the examples from the test
        # data include an empty string instead :/, so we include it in the checks
        if (street_name := address.get("streetName")) in (None, ""):
            formatted_address = None
        elif (house_number := address.get("houseNumber")) in (None, ""):
            formatted_address = street_name
        elif (suffix := address.get("houseNumberSuffix")) in (None, ""):
            formatted_address = f"{street_name} {house_number}"
        else:
            formatted_address = f"{street_name} {house_number}{suffix}"

        return Location(
            identifier=location["id"],
            name=location.get("description"),
            address=formatted_address,
            city=address.get("city"),
            postalcode=address.get("postalCode"),
        )

    @with_graceful_default(default=[])
    def get_locations(
        self,
        products: list[Product] | None = None,
    ) -> list[Location]:
        if products is None:
            path = "location"
            params = None
        else:
            path = "location/forappointment"
            # Note passing the same query parameter multiple times is intended behaviour
            params = [
                ("selectedActivityId", product.identifier) for product in products
            ]

        client = self.client
        with log_api_errors("locations_retrieval_failure"):
            response = client.get(path, params)
            response.raise_for_status()

        locations = [self._create_location(location) for location in response.json()]

        return locations

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
