from typing import Any

from django.utils.translation import get_language

import structlog
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingClient

from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


def JccRestClient() -> "Client":
    """
    Create a Jcc Rest client instance from the database configuration.
    """
    config = JccRestConfig.get_solo()
    if (service := config.service) is None:
        raise NoServiceConfigured("No Jcc Rest service defined, aborting.")
    assert isinstance(service, Service)
    return build_client(service, client_factory=Client)


class Client(LoggingClient):
    """
    Client implementation for Jcc Rest plugin.
    """

    # TODO
    # See if it's possible(and needed) to fix the type hints concerning the return of
    # each method (typed dicts for example). This requires proper documentation from JCC
    # (API specification is not enough).

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add the required header for the desired language
        self.headers["language"] = get_language()

    def retrieve_location_details(self, location_identifier: str) -> dict[str, Any]:
        """Retrieve the extra location details based on the location UUID."""
        endpoint = f"location/{location_identifier}"
        response = self.get(endpoint)
        response.raise_for_status()
        return response.json()

    def list_customer_required_fields(self, product_uuids: list[str]) -> dict[str, Any]:
        """Retrieve all the required customer field names based on the products UUIDs."""
        response = self.get(
            "customer/customerfields/required",
            params={"selectedActivityId": product_uuids},
        )
        response.raise_for_status()
        return response.json()

    def book_appointment(self, appointment_data: dict[str, str]) -> dict[str, Any]:
        """Book an appointment."""
        response = self.post("appointment", json=appointment_data)
        response.raise_for_status()
        return response.json()

    def retrieve_appointment_details(
        self, appointment_identifier: str
    ) -> dict[str, Any]:
        """Retrieve all the appointment's related information."""
        response = self.get("appointment", params={"uuid": appointment_identifier})
        response.raise_for_status()
        return response.json()

    def retrieve_appointment_qr_code(
        self, appointment_identifier: str
    ) -> dict[str, Any]:
        """Get the appointment's qr code string based on the appointment UUID."""
        response = self.get("appointment", params={"uuid": appointment_identifier})
        response.raise_for_status()
        return response.json()

    def cancel_appointment(self, appointment_identifier: str) -> dict[str, Any]:
        """Cancel an appointment."""
        response = self.delete("appointment", params={"uuid": appointment_identifier})
        response.raise_for_status()
        return response.json()
