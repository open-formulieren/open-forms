import json
import logging
from datetime import date, datetime, time

from openforms.appointments.contrib.qmatic.models import QmaticConfig

from ..base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    Plugin for Qmatic Orchestra Calendar Public Appointment API (july 2017)
    """

    def __init__(self):
        config = QmaticConfig.get_solo()
        if not config.service:
            logger.warning("No service defined for Qmatic")
            return

        self.client = config.service.build_client()
        self.api_root = config.service.api_root

    def get_available_products(self, current_products: list = None) -> list:
        """
        NOTE: The API does not support making an appointment for multiple
        products. The `current_products` argument is ignored.
        """
        try:
            response = self.client.get(f"{self.api_root}services")
            if response.status_code != 200:
                raise Exception(response.text)
        except Exception as e:
            logger.exception(e)
            return []

        return [
            AppointmentProduct(entry["publicId"], entry["name"])
            for entry in response.json()["serviceList"]
        ]

    def get_locations(self, products: list) -> list:
        if len(products) != 1:
            return []

        product_id = products[0].identifier

        try:
            response = self.client.get(f"{self.api_root}services/{product_id}/branches")
            if response.status_code != 200:
                raise Exception(response.text)
        except Exception as e:
            logger.exception(e)
            return []

        return [
            AppointmentLocation(entry["publicId"], entry["name"])
            for entry in response.json()["branchList"]
        ]

    def get_dates(
        self,
        products: list,
        location: AppointmentLocation,
        start_at: date = None,
        end_at: date = None,
    ) -> list:
        """
        NOTE: The API does not support getting dates between a start and end
        date. The `start_at` and `end_at` arguments are ingored.
        """
        if len(products) != 1:
            return []

        product_id = products[0].identifier

        try:
            response = self.client.get(
                f"{self.api_root}branches/{location.identifier}/services/{product_id}/dates"
            )
            if response.status_code != 200:
                raise Exception(response.text)
        except Exception as e:
            logger.exception(e)
            return []

        return [
            datetime.fromisoformat(entry).date() for entry in response.json()["dates"]
        ]

    def get_times(
        self, products: list, location: AppointmentLocation, day: date
    ) -> list:
        if len(products) != 1:
            return []

        product_id = products[0].identifier

        try:
            response = self.client.get(
                f"{self.api_root}branches/{location.identifier}/services/{product_id}/dates/{day}/times"
            )
            if response.status_code != 200:
                raise Exception(response.text)
        except Exception as e:
            logger.exception(e)
            return []

        return [
            datetime.combine(day, time.fromisoformat(entry))
            for entry in response.json()["times"]
        ]

    def create_appointment(
        self,
        products: list,
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
                f"{self.api_root}branches/{location.identifier}/services/{product_id}/dates/{start_at.date()}/times/{start_at.strftime('%H:%M')}/book",
                data,
            )
            if response.status_code not in [200, 201]:
                raise Exception(response.text)
            return response.json()["publicId"]

        except Exception as e:
            logger.exception(e)
            raise

    def delete_appointment(self, identifier: str) -> bool:
        try:
            response = self.client.delete(f"{self.api_root}appointments/{identifier}")
            if response.status_code != 200:
                raise Exception(response.text)
        except Exception as e:
            logger.exception(e)
            return False

        return True
