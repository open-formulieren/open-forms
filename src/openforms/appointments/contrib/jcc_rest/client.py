from collections.abc import Collection, Sequence
from contextlib import contextmanager
from datetime import date, datetime

from django.utils.timezone import make_aware
from django.utils.translation import get_language

import requests
import structlog
from requests import JSONDecodeError
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingClient
from openforms.utils.date import TIMEZONE_AMS

from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig
from .types import Activity, Location, Version

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
            except JSONDecodeError:
                pass
        logger.exception(event, response_content=content, exc_info=exc)
        raise GracefulJccRestException("JCC REST API call failed") from exc
    except Exception as exc:  # pragma: nocover
        raise JccRestException from exc


class Client(LoggingClient):
    """
    Client implementation for Jcc Rest plugin.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add the required header for the desired language
        self.headers["language"] = get_language()

    def get_version(self) -> Version:
        """Get JCC-Afspraken version."""
        with log_api_errors("version_retrieval_failure"):
            response = self.get("version")
            response.raise_for_status()

        return response.json()

    def get_activity_list_for_appointment(self, location_id: str) -> Sequence[Activity]:
        """Get a list of available activities for an appointment."""
        params = {"locationId": location_id} if location_id else {}

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_additional_activity_list_for_appointment(
        self, activity_ids: Collection[str], location_id: str
    ) -> Sequence[Activity]:
        """Get a list of additional activities based on selected activities."""
        # Passing the activity ids like this will repeat this query parameter for each
        # id in the list
        params = {
            "selectedActivityId": activity_ids,
            "includeSelectedActivities": False,
        }
        if location_id:
            params["locationId"] = location_id

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment/additional", params=params)
            response.raise_for_status()

        return response.json()

    def get_location_list(self) -> Sequence[Location]:
        """Get list of locations."""
        with log_api_errors("locations_retrieval_failure"):
            response = self.get("location")
            response.raise_for_status()

        return response.json()

    def get_location_list_for_appointment(
        self, activity_ids: Collection[str]
    ) -> Sequence[Location]:
        """
        Get list of locations available for appointment based on selected activities.
        """
        with log_api_errors("locations_retrieval_failure"):
            response = self.get(
                "location/forappointment", params={"selectedActivityId": activity_ids}
            )
            response.raise_for_status()

        return response.json()

    def get_appointment_date_range_for_activities(
        self, activity_ids: Collection[str]
    ) -> tuple[date, date]:
        """
        Get the available date range for an appointment based on provided activities.
        """
        with log_api_errors("date_range_retrieval_failure"):
            response = self.get(
                "activity/appointmentdaterange",
                params={"activityId": activity_ids},
            )
            response.raise_for_status()

        # Format min and max dates
        res_json = response.json()
        min_date = datetime.fromisoformat(res_json["minDate"]).date()
        max_date = datetime.fromisoformat(res_json["maxDate"]).date()

        return min_date, max_date

    def get_available_times_for_appointment(
        self,
        location_id: str,
        from_date: date,
        to_date: date,
        activities: Collection[tuple[str, int]],
    ) -> Sequence[datetime]:
        """Get a list of available times for an appointment.

        :param activities: Collection of tuples containing an activity ID with an
          amount.
        """
        activity_ids, amounts = zip(*activities, strict=False)
        params = {
            "locationId": location_id,
            "fromDate": from_date.isoformat(),
            "toDate": to_date.isoformat(),
            "activityId": activity_ids,
            "amount": amounts,
        }
        with log_api_errors("available_times_retrieval_failure"):
            response = self.get("appointment/availabletimelist", params=params)
            response.raise_for_status()

        # The received times do not include timezone information, so we assume
        # Europe/Amsterdam.
        return [
            make_aware(datetime.fromisoformat(date_string), TIMEZONE_AMS)
            for date_string in response.json()["availableTimesList"]
        ]


def JccRestClient() -> Client:
    """
    Create a Jcc Rest client instance from the database configuration.
    """
    config = JccRestConfig.get_solo()
    if (service := config.service) is None:
        raise NoServiceConfigured("No Jcc Rest service defined, aborting.")
    assert isinstance(service, Service)
    return build_client(service, client_factory=Client)
