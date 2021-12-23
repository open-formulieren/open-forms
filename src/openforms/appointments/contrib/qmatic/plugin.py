import json
import logging
from datetime import date, datetime, time
from typing import List, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _

from dateutil.parser import isoparse
from requests.exceptions import RequestException

from openforms.plugins.exceptions import InvalidPluginConfiguration

from ...base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from .client import QmaticClient, QmaticException

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    Plugin for Qmatic Orchestra Calendar Public Appointment API (july 2017)

    Website: https://www.qmatic.com/
    """

    identifier = "Qmatic-Plugin"
    verbose_name = "Qmatic-Plugin"

    def __init__(self):
        self.client = QmaticClient()

    def get_available_products(
        self, current_products: Optional[List[AppointmentProduct]] = None
    ) -> List[AppointmentProduct]:
        """
        Retrieve all available products and services to create an appointment for.

        NOTE: The API does not support making an appointment for multiple
        products. The ``current_products`` argument is ignored.
        """
        try:
            response = self.client.get("services")
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception("Could not retrieve available products", exc_info=e)
            return []
        except Exception as exc:
            raise AppointmentException from exc

        # NOTE: Filter out products that are not active or public.

        return [
            AppointmentProduct(entry["publicId"], entry["name"])
            for entry in response.json()["serviceList"]
            if entry["publicEnabled"] and entry["active"]
        ]

    def get_locations(
        self, products: List[AppointmentProduct]
    ) -> List[AppointmentLocation]:
        if len(products) > 1:
            logger.warning("Attempt to retrieve locations for more than one product.")

        product_id = products[0].identifier

        try:
            response = self.client.get(f"services/{product_id}/branches")
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            logger.exception(
                "Could not retrieve locations for product '%s'", product_id, exc_info=e
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        # NOTE: Filter out locations that do not have a postal code to prevent
        # non-physical addresses.

        return [
            AppointmentLocation(entry["publicId"], entry["name"])
            for entry in response.json()["branchList"]
            if entry["addressZip"]
        ]

    def get_dates(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: Optional[date] = None,
        end_at: Optional[date] = None,
    ) -> List[date]:
        """
        Retrieve all available dates for given ``products`` and ``location``.

        NOTE: The API does not support getting dates between a start and end
        date. The `start_at` and `end_at` arguments are ingored.
        """
        if len(products) != 1:
            return []

        product_id = products[0].identifier

        try:
            response = self.client.get(
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
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        day: date,
    ) -> List[datetime]:
        if len(products) != 1:
            return []

        product_id = products[0].identifier

        try:
            response = self.client.get(
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

    def create_appointment(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: datetime,
        client: AppointmentClient,
        remarks: str = None,
    ) -> str:
        if len(products) != 1:
            return []

        product_id = products[0].identifier
        product_name = products[0].name

        data = {
            "title": f"Open Formulieren: {product_name}",
            "customer": {
                # "firstName" : "Voornaam",
                "lastName": client.last_name,
                # "email" : "test@test.com",
                # "phone" : "06-11223344",
                # "addressLine1" : "Straatnaam 1",
                # "addressCity" : "Plaatsnaam",
                # "addressState" : "Zuid Holland",
                # "addressZip" : "1111AB",
                # "addressCountry" : "Nederland",
                # "identificationNumber" : "1234567890",
                "dateOfBirth": client.birthdate,
            },
            "notes": remarks,
        }

        start_date = start_at.strftime("%Y-%m-%d")
        start_time = start_at.strftime("%H:%M")
        url = (
            f"branches/{location.identifier}/services/{product_id}/"
            f"dates/{start_date}/times/{start_time}/book"
        )
        try:
            response = self.client.post(url, json.dumps(data, cls=DjangoJSONEncoder))
            response.raise_for_status()
            return response.json()["publicId"]
        except (QmaticException, RequestException, KeyError) as exc:
            raise AppointmentCreateFailed(
                "Could not create appointment for products '%s' at location '%s' starting at %s: %s",
                product_id,
                location,
                start_at,
                exc,
            )
        except Exception as exc:
            raise AppointmentException from exc

    def delete_appointment(self, identifier: str) -> None:
        try:
            response = self.client.delete(f"appointments/{identifier}")
            if response.status_code == 404:
                raise AppointmentDeleteFailed(
                    "Could not delete appointment: %s", identifier
                )

            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            raise AppointmentDeleteFailed(e)

    def get_appointment_details(self, identifier: str) -> str:
        try:
            response = self.client.get(f"appointments/{identifier}")
            response.raise_for_status()

            details = response.json()["appointment"]

            result = AppointmentDetails(
                identifier=identifier,
                products=[
                    AppointmentProduct(identifier=entry["publicId"], name=entry["name"])
                    for entry in details["services"]
                ],
                location=AppointmentLocation(
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
        try:
            response = self.client.get("services")
            response.raise_for_status()
        except (QmaticException, RequestException) as e:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )
