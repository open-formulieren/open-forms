import json
from collections import Counter
from collections.abc import Callable
from contextlib import contextmanager
from datetime import date, datetime
from functools import wraps
from typing import ParamSpec
from zoneinfo import ZoneInfo

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from dateutil.parser import isoparse
from requests.exceptions import RequestException

from openforms.formio.typing import Component
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ...base import AppointmentDetails, BasePlugin, CustomerDetails, Location, Product
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ...registry import register
from .client import FullServiceDict, QmaticClient
from .constants import FIELD_TO_FORMIO_COMPONENT, CustomerFields
from .exceptions import GracefulQmaticException, QmaticException
from .models import QmaticConfig

logger = structlog.stdlib.get_logger(__name__)

_CustomerDetails = CustomerDetails[CustomerFields]


@contextmanager
def log_api_errors(event: str):
    try:
        yield
    except (QmaticException, RequestException) as exc:
        logger.exception(event, exc_info=exc)
        raise GracefulQmaticException("API call failed") from exc
    except Exception as exc:
        raise QmaticException from exc


Param = ParamSpec("Param")


def with_graceful_default[T](default: T):  # pyright: ignore[reportInvalidTypeVarUse]
    def decorator(func: Callable[Param, T]) -> Callable[Param, T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except GracefulQmaticException:
                return default

        return wrapper

    return decorator


@register("qmatic")
class QmaticAppointment(BasePlugin[CustomerFields]):
    """
    Plugin for Qmatic Orchestra Calendar Public Appointment API (july 2017)

    Website: https://www.qmatic.com/
    """

    verbose_name = _("Qmatic")
    # See "Book an appointment for multiple customers and multiple services" in the
    # documentation.
    supports_multiple_products = True

    @staticmethod
    def _count_products(products: list[Product]) -> tuple[list[str], int]:
        products_counter = Counter()
        for product in products:
            products_counter.update({product.identifier: product.amount})

        # grab the amount of the most common product - this determines the total number
        # of customers for the appointment (see docstring explanation).
        num_customers = products_counter.most_common(1)[0][1]
        unique_product_ids = list(products_counter.keys())
        return (unique_product_ids, num_customers)

    @with_graceful_default(default=[])
    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        """
        Retrieve all available products and services to create an appointment for.

        Qmatic has a couple of possible endpoints for this, most notably one returning
        a flat list of products (all or filtered by branch) and two others that return
        product groups. The product groups dictate which products can be booked together.

        We have to use all of these, since the flat list of products contains additional
        information like whether a product is public and/or active, which is not included
        in the service groups.

        The service groups per branch requires v2 API client, the rest can be done with
        the v1 client.
        """
        current_products = current_products or []

        # enter context block to use connection pooling
        with QmaticClient() as client:
            with log_api_errors("products_retrieval_failure"):
                services = client.list_services(location_id=location_id)

            # only consider services publicly available and active
            available_services: list[FullServiceDict] = [
                service
                for service in services
                if service["publicEnabled"] and service["active"]
            ]

            # if another product is selected already, we need to filter down the services
            # to only those in the same service group(s). Through trial and error, it's
            # clear that this service ID parameter can be repeated, even though the
            # documentation does not explicitly mention it.
            group_service_ids = [product.identifier for product in current_products]
            with (
                structlog.contextvars.bound_contextvars(
                    group_service_ids=group_service_ids
                ),
                log_api_errors("product_service_groups_retrieval_failure"),
            ):
                service_groups = (
                    client.list_service_groups(
                        group_service_ids, location_id=location_id
                    )
                    if group_service_ids
                    else None
                )

        if service_groups is not None:
            # filter out possible services based on the service groups
            allowed_service_ids = {
                service["publicId"]
                for group in service_groups
                for service in group["services"]
            }
            available_services = [
                service
                for service in available_services
                if service["publicId"] in allowed_service_ids
            ]

        return [
            Product(entry["publicId"], entry["name"]) for entry in available_services
        ]

    @with_graceful_default(default=[])
    def get_locations(
        self,
        products: list[Product] | None = None,
    ) -> list[Location]:
        """
        Retrieve all available locations.

        When supplying multiple products, the caller must ensure that these products
        can be booked together. This is the case if you use
        :meth:`get_available_products`. Only products that are in the same service
        group can be booked together.

        It does not appear that the Qmatic API supports retrieving a list of available
        branches with more than one service ID parameter, so we must grab a "random"
        product to get the ID. If any products are provided at all, then we are
        guaranteed that index 0 yields a product we can use to query locations for.
        """
        products = products or []
        product_ids = [product.identifier for product in products]

        client = QmaticClient()

        # if multiple products are provided, we use the first one as there's no way to
        # provide multiple products in the query
        if len(product_ids) > 1:
            logger.debug(
                "limit_location_retrieval_products_filter",
                product_ids=product_ids,
            )
        endpoint = f"services/{product_ids[0]}/branches" if product_ids else "branches"
        with (
            structlog.contextvars.bound_contextvars(endpoint=endpoint),
            log_api_errors("locations_retrieval_failure"),
        ):
            response = client.get(endpoint)
            response.raise_for_status()

        # NOTE: Filter out locations that do not have a postal code to prevent
        # non-physical addresses.

        return [
            Location(entry["publicId"], entry["name"])
            for entry in response.json()["branchList"]
            if entry["addressZip"]
        ]

    @with_graceful_default(default=[])
    def get_dates(
        self,
        products: list[Product],
        location: Location,
        start_at: date | None = None,
        end_at: date | None = None,
    ) -> list[date]:
        """
        Retrieve all available dates for given ``products`` and ``location``.

        From the documentation:

            numberOfCustomers will be used on all services when calculating the
            appointment duration. For example, a service with Duration of 10 minutes and
            additionalCustomerDuration of 5 minutes will result in an appointment
            duration of 50 when minutes for 4 customers and 2 services.

        The example given shows that it makes little sense to attach number of customers
        to a particular product/service. E.g. if you have amount=2 for product 1 and
        amount=3 for product 2, booking the appointment for 3 customers results in time
        for 3 people for each product (which is more than you need). Using 5 customers (
        2 + 3) would result in time reserved for 10 people and is incorrect in this
        situation.

        .. note:: The API does not support getting dates between a start and end
           date. The `start_at` and `end_at` arguments are ingored.
        """
        assert products, "Can't retrieve dates without having product information"
        unique_product_ids, num_customers = self._count_products(products)

        with (
            log_api_errors("dates_retrieval_failure"),
            QmaticClient() as client,
        ):
            return client.list_dates(
                location_id=location.identifier,
                service_ids=unique_product_ids,
                num_customers=num_customers,
            )

    @with_graceful_default(default=[])
    def get_times(
        self,
        products: list[Product],
        location: Location,
        day: date,
    ) -> list[datetime]:
        assert products, "Can't retrieve dates without having product information"
        unique_product_ids, num_customers = self._count_products(products)

        with (
            log_api_errors("times_retrieval_failure"),
            QmaticClient() as client,
        ):
            return client.list_times(
                location_id=location.identifier,
                day=day,
                service_ids=unique_product_ids,
                num_customers=num_customers,
            )

    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> tuple[list[Component], None]:
        config = QmaticConfig.get_solo()
        components = [
            FIELD_TO_FORMIO_COMPONENT[field]
            for field in config.required_customer_fields
        ]
        return components, None

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: _CustomerDetails,
        remarks: str = "",
    ) -> str:
        assert products, "Can't book for empty products"

        product_names = ", ".join(sorted({product.name for product in products}))
        unique_product_ids, num_customers = self._count_products(products)

        body = {
            "title": f"Open Formulieren: {product_names}",
            # we repeat the same customer information for every customer, as we currently
            # don't support getting the contact details for each individual customer
            "customers": [
                {choice: value for choice, value in client.details.items() if value}
            ]
            * num_customers,
            "services": [{"publicId": product_id} for product_id in unique_product_ids],
            "notes": remarks,
        }

        location_id = location.identifier

        with QmaticClient() as api_client:
            # Ensure that we get the appointment time in the timezone of the branch we're booking for
            branch = api_client.get_branch(location_id)
            branch_timezone = ZoneInfo(branch["timeZone"])
            if not timezone.is_naive(start_at):
                start_at = timezone.make_naive(start_at, timezone=branch_timezone)

            start_date = start_at.date().isoformat()
            start_time = start_at.strftime("%H:%M")

            # Build the endpoint with all relevant information, see
            # "Book an appointment for multiple customers and multiple services" in the
            # docs.
            endpoint = (
                f"v2/branches/{location_id}/dates/{start_date}/times/{start_time}/book"
            )
            try:
                response = api_client.post(
                    endpoint, data=json.dumps(body, cls=DjangoJSONEncoder)
                )
                response.raise_for_status()
                return response.json()["publicId"]
            except (QmaticException, RequestException, KeyError) as exc:
                logger.error(
                    "appointment_create_failure",
                    products=unique_product_ids,
                    location=location.identifier,
                    start_at=start_at,
                    exc_info=exc,
                )
                raise AppointmentCreateFailed("Could not create appointment") from exc
            except Exception as exc:
                raise AppointmentCreateFailed(
                    "Unexpected appointment create failure"
                ) from exc

    def delete_appointment(self, identifier: str) -> None:
        client = QmaticClient()
        try:
            response = client.delete(f"appointments/{identifier}")
            if response.status_code == 404:
                raise AppointmentDeleteFailed(
                    "Could not delete appointment: %s", identifier
                )

            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            raise AppointmentDeleteFailed(e)

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        client = QmaticClient()
        try:
            response = client.get(f"appointments/{identifier}")
            response.raise_for_status()

            details = response.json()["appointment"]

            result = AppointmentDetails(
                identifier=identifier,
                products=[
                    Product(identifier=entry["publicId"], name=entry["name"])
                    for entry in details["services"]
                ],
                location=Location(
                    identifier=details["branch"]["publicId"],
                    name=details["branch"]["name"],
                    address=" ".join(
                        [
                            details["branch"]["addressLine1"] or "",
                            details["branch"]["addressLine2"] or "",
                        ]
                    ),
                    postalcode=details["branch"]["addressZip"],
                    city=details["branch"]["addressCity"],
                ),
                start_at=isoparse(details["start"]),
                end_at=isoparse(details["end"]),
                remarks=details["notes"],
                other={},
            )

            return result

        except (QmaticException, RequestException, KeyError) as e:
            raise AppointmentException(e)

    def check_config(self):
        client = QmaticClient()
        try:
            response = client.get("services")
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:qmatic_qmaticconfig_change",
                    args=(QmaticConfig.singleton_instance_id,),
                ),
            ),
        ]
