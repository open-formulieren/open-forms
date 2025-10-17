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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add the required header for the desired language
        self.headers["language"] = get_language()

    def list_customer_required_fields(self, product_uuids: list[str]):
        """Retrieve all the required customer field names based on the products UUIDs."""
        response = self.get(
            "customer/customerfields/required",
            params={"selectedActivityId": product_uuids},
        )

        response.raise_for_status()
        return response.json()

    # TODO
    # Update type hint for appointment_data (more explicit) if possible

    def book_appointment(self, appointment_data: dict[str, str]):
        """Book an appointment."""
        response = self.post("appointment", json=appointment_data)
        from celery.contrib import rdb

        rdb.set_trace()
        response.raise_for_status()
        return response.json()
