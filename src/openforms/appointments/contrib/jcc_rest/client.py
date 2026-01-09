from collections.abc import Sequence
from contextlib import contextmanager
from datetime import date

from django.utils.translation import get_language

import requests
import structlog
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingClient

from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig
from .types import (
    CancelledAppointment,
    CreatedAppointment,
    CustomerFields,
    ExistingAppointment,
    Location,
)

logger = structlog.stdlib.get_logger(__name__)


class NoServiceConfigured(RuntimeError):
    pass


@contextmanager
def log_api_errors(event: str):
    try:
        yield
    except requests.RequestException as exc:
        content = None
        if exc.response is not None:
            try:
                content = exc.response.json()
            except ValueError:
                pass

        logger.exception(event, response_content=content, exc_info=exc)
        raise GracefulJccRestException("JCC REST API call failed") from exc
    except Exception as exc:
        raise JccRestException from exc


class Client(LoggingClient):
    """
    Client implementation for Jcc Rest plugin.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add the required header for the desired language
        self.headers["language"] = get_language()

    def get_location(self, location_identifier: str) -> Location:
        """Retrieve the extra location details based on the location UUID."""
        endpoint = f"location/{location_identifier}"

        with log_api_errors("location_details_retrieval_failure"):
            response = self.get(endpoint)
            response.raise_for_status()

        return response.json()

    def get_required_customer_fields(
        self, product_uuids: Sequence[str]
    ) -> CustomerFields:
        """Retrieve all the required customer field names based on the products UUIDs."""
        params = {"selectedActivityId": product_uuids}

        with log_api_errors("required_customer_fields_failure"):
            response = self.get(
                "customer/customerfields/required",
                params=params,
            )
            response.raise_for_status()

        return response.json()

    def add_appointment(self, appointment_data: dict[str, str]) -> CreatedAppointment:
        """Book an appointment."""
        with log_api_errors("book_appointment_failure"):
            response = self.post("appointment", json=appointment_data)
            response.raise_for_status()

        return response.json()

    def get_appointment(self, appointment_identifier: str) -> ExistingAppointment:
        """Retrieve all the appointment's related information."""
        params = {"id": appointment_identifier}

        with log_api_errors("appointment_details_retrieval_failure"):
            response = self.get("appointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_duration_for_appointment(
        self,
        date: date,
        activity_ids: Sequence[str],
        amounts: Sequence[int],
    ) -> int:
        """Retrieve the duration (in minutes) for an appointment."""
        assert len(activity_ids) == len(amounts), (
            "Number of activity IDs and amounts must be equal"
        )

        params = []
        for id_, amount in zip(activity_ids, amounts, strict=False):
            params.append(("activityId", id_))
            params.append(("amount", amount))

        params.append(("dateTime", date.isoformat()))

        with log_api_errors("appointment_duration_retrieval_failure"):
            response = self.get("appointment/calculateduration", params=params)
            response.raise_for_status()

        return response.json()

    def get_appointment_qr_code(self, appointment_identifier: str) -> str:
        """Get the appointment's qr code string based on the appointment UUID."""
        params = {"id": appointment_identifier}

        with log_api_errors("appointment_qr_code_retrieval_failure"):
            response = self.get("appointment", params=params)
            response.raise_for_status()

        return response.json()

    def cancel_appointment(self, appointment_identifier: str) -> CancelledAppointment:
        """Cancel an appointment."""
        params = {"id": appointment_identifier}

        with log_api_errors("cancel_appointment_failure"):
            response = self.delete("appointment", params=params)
            response.raise_for_status()

        return response.json()


def JccRestClient() -> Client:
    """
    Create a Jcc Rest client instance from the database configuration.
    """
    config = JccRestConfig.get_solo()
    if (service := config.service) is None:
        raise NoServiceConfigured("No Jcc Rest service defined, aborting.")
    assert isinstance(service, Service)
    return build_client(service, client_factory=Client)
