import logging
from datetime import date, datetime, time
from typing import List, Optional

from requests.exceptions import RequestException
from zds_client import ClientError

from ...base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from .client import QmaticClient

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    Plugin for Qmatic Orchestra Calendar Public Appointment API (july 2017)

    Website: https://www.qmatic.com/
    """

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
        except (ClientError, RequestException) as e:
            logger.exception("Could not retrieve available products", exc_info=e)
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            AppointmentProduct(entry["publicId"], entry["name"])
            for entry in response.json()["serviceList"]
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
        except (ClientError, RequestException) as e:
            logger.exception(
                "Could not retrieve locations for product '%s'", product_id, exc_info=e
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            AppointmentLocation(entry["publicId"], entry["name"])
            for entry in response.json()["branchList"]
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
        except (ClientError, RequestException) as e:
            logger.exception(
                "Could not retrieve dates for product '%s' at location '%s'",
                product_id,
                location,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            datetime.fromisoformat(entry).date() for entry in response.json()["dates"]
        ]

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
        except (ClientError, RequestException) as e:
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

        try:
            response = self.client.post(
                f"branches/{location.identifier}/services/{product_id}/dates/{start_at.strftime('%Y-%m-%d')}/times/{start_at.strftime('%H:%M')}/book",
                data,
            )
            response.raise_for_status()
            return response.json()["publicId"]
        except (ClientError, RequestException, KeyError) as e:
            raise AppointmentCreateFailed(
                "Could not create appointment for products '%s' at location '%s' starting at %s",
                product_id,
                location,
                start_at,
            )
        except Exception as exc:
            raise AppointmentException from exc

    def delete_appointment(self, identifier: str) -> None:
        try:
            response = self.client.delete(f"appointments/{identifier}")
            if response.status_code == 404:
                raise AppointmentDeleteFailed(
                    "Could not delete appointment",
                )

            response.raise_for_status()
        except (ClientError, RequestException) as e:
            raise AppointmentDeleteFailed(e)
