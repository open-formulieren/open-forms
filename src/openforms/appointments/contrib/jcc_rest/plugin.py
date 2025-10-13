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
from .constants import CustomerFields
from .exceptions import GracefulJccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)

Param = ParamSpec("Param")
T = TypeVar("T")
FuncT = Callable[Param, T]


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
