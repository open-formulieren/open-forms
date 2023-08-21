import json
import logging
import warnings
from datetime import date, datetime, time

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import pytz
from dateutil.parser import isoparse
from requests.exceptions import RequestException

from openforms.formio.typing import Component
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ...base import (
    AppointmentDetails,
    BasePlugin,
    Customer,
    CustomerDetails,
    Location,
    Product,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ...registry import register
from .client import QmaticClient, QmaticException
from .constants import FIELD_TO_FORMIO_COMPONENT, CustomerFields
from .models import QmaticConfig

logger = logging.getLogger(__name__)

_CustomerDetails = CustomerDetails[CustomerFields]

TIMEZONE_AMS = pytz.timezone("Europe/Amsterdam")


@register("qmatic")
class QmaticAppointment(BasePlugin[CustomerFields]):
    """
    Plugin for Qmatic Orchestra Calendar Public Appointment API (july 2017)

    Website: https://www.qmatic.com/
    """

    verbose_name = _("Qmatic")
    # See "Book an appointment for multiple customers and multiple services" in the
    # documentation. Qmatic *does* support it, but there are no stakeholders anymore for
    # this plugin so we only provide the legacy (pre 2.3.0) functionality.
    supports_multiple_products = False

    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        """
        Retrieve all available products and services to create an appointment for.

        NOTE: The API does not support making an appointment for multiple
        products. The ``current_products`` argument is ignored.
        """
        client = QmaticClient()
        endpoint = f"branches/{location_id}/services" if location_id else "services"
        try:
            response = client.get(endpoint)
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception("Could not retrieve available products", exc_info=e)
            return []
        except Exception as exc:
            raise AppointmentException from exc

        # NOTE: Filter out products that are not active or public.

        return [
            Product(entry["publicId"], entry["name"])
            for entry in response.json()["serviceList"]
            if entry["publicEnabled"] and entry["active"]
        ]

    def get_locations(
        self,
        products: list[Product] | None = None,
    ) -> list[Location]:
        products = products or []
        product_ids = [product.identifier for product in products]

        client = QmaticClient()

        if not product_ids:
            endpoint = "branches"
        else:
            if len(product_ids) > 1:
                logger.warning(
                    "Attempt to retrieve locations for more than one product. Using "
                    "the first ID to limit locations."
                )
            endpoint = f"services/{product_ids[0]}/branches"

        try:
            response = client.get(endpoint)
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception(
                "Could not retrieve locations for product, using API endpoint '%s'",
                endpoint,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        # NOTE: Filter out locations that do not have a postal code to prevent
        # non-physical addresses.

        return [
            Location(entry["publicId"], entry["name"])
            for entry in response.json()["branchList"]
            if entry["addressZip"]
        ]

    def get_dates(
        self,
        products: list[Product],
        location: Location,
        start_at: date | None = None,
        end_at: date | None = None,
    ) -> list[date]:
        """
        Retrieve all available dates for given ``products`` and ``location``.

        NOTE: The API does not support getting dates between a start and end
        date. The `start_at` and `end_at` arguments are ingored.
        """
        if len(products) != 1:
            return []

        client = QmaticClient()
        product_id = products[0].identifier

        try:
            response = client.get(
                f"branches/{location.identifier}/services/{product_id}/dates"
            )
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception(
                "Could not retrieve dates for product '%s' at location '%s'",
                product_id,
                location,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [isoparse(entry).date() for entry in response.json()["dates"]]

    def get_times(
        self,
        products: list[Product],
        location: Location,
        day: date,
    ) -> list[datetime]:
        if len(products) != 1:
            return []

        client = QmaticClient()
        product_id = products[0].identifier

        try:
            response = client.get(
                f"branches/{location.identifier}/services/{product_id}/dates/{day.strftime('%Y-%m-%d')}/times"
            )
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception(
                "Could not retrieve times for product '%s' at location '%s' on %s",
                product_id,
                location,
                day,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            datetime.combine(day, time.fromisoformat(entry))
            for entry in response.json()["times"]
        ]

    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> list[Component]:
        config = QmaticConfig.get_solo()
        assert isinstance(config, QmaticConfig)
        components = [
            FIELD_TO_FORMIO_COMPONENT[field]
            for field in config.required_customer_fields
        ]
        return components

    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: _CustomerDetails | Customer,
        remarks: str = "",
    ) -> str | None:
        warnings.warn(
            "The QMatic plugin is deprecated and will be removed in Open Forms 3.0",
            DeprecationWarning,
        )

        qmatic_client = QmaticClient()
        if len(products) != 1:
            logger.warning(
                "The QMatic plugin (currently) does not support booking appointments "
                "with multiple products or services",
                extra={"products": products},
            )
            return

        product_id = products[0].identifier
        product_name = products[0].name

        # Phasing out Customer in favour of CustomerDetails, so convert to the new type
        if isinstance(client, Customer):
            warnings.warn(
                "Fixed customer fields via the Customer class are deprecated, use "
                "dynamic CustomerDetails with 'get_required_customer_fields' instead.",
                DeprecationWarning,
            )
            client = _CustomerDetails(
                details={
                    CustomerFields.last_name: client.last_name,
                    CustomerFields.birthday: client.birthdate.isoformat(),
                    CustomerFields.first_name: client.initials or "",
                    CustomerFields.phone_number: client.phonenumber or "",
                }
            )

        data = {
            "title": f"Open Formulieren: {product_name}",
            "customer": {
                choice.value: value for choice, value in client.details.items() if value
            },
            "notes": remarks,
        }

        if not timezone.is_naive(start_at):
            start_at = timezone.make_naive(start_at, timezone=TIMEZONE_AMS)

        start_date = start_at.strftime("%Y-%m-%d")
        start_time = start_at.strftime("%H:%M")
        url = (
            f"branches/{location.identifier}/services/{product_id}/"
            f"dates/{start_date}/times/{start_time}/book"
        )
        try:
            response = qmatic_client.post(
                url, data=json.dumps(data, cls=DjangoJSONEncoder)
            )
            response.raise_for_status()
            return response.json()["publicId"]
        except (QmaticException, RequestException, KeyError) as exc:
            logger.error(
                "Could not create appointment for product '%s' at location '%s' starting at %s",
                product_id,
                location,
                start_at,
                exc_info=exc,
                extra={
                    "product_ids": product_id,
                    "location": location.identifier,
                    "start_time": start_at,
                },
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
