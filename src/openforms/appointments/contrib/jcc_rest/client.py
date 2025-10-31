from collections.abc import Collection, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from typing import NotRequired, TypedDict

from django.utils.timezone import make_aware
from django.utils.translation import get_language

import requests
import structlog
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingClient
from openforms.utils.date import TIMEZONE_AMS

from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)


# Source for the typed dict definitions:
# https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
# Asked JCC: "string or null" means that the field can be missing entirely as well
# Note that the documentation defines a "revision" key for most of these dicts, but
# NONE of the example data from their test environment include this, so decided to leave
# it out
class Version(TypedDict):
    warpApiVersion: NotRequired[str]
    afsprakenVersion: NotRequired[str]


class Activity(TypedDict):
    id: str
    number: NotRequired[int]  # will be replaced by id eventually
    code: NotRequired[str]  # this is not used anymore actually
    description: NotRequired[str]
    necessities: NotRequired[str]
    appointmentDuration: int
    maxCountForEvent: NotRequired[int]
    activityGroupId: NotRequired[str]
    synonyms: NotRequired[list[str]]


class PhoneNumber(TypedDict):
    auditId: str
    id: str
    value: NotRequired[str]


class PhoneNumberType(TypedDict):
    auditId: str
    id: str
    name: NotRequired[str]
    description: NotRequired[str]


class LocationPhoneNumber(TypedDict):
    auditId: str
    id: str
    phoneNumber: PhoneNumber
    phoneNumberType: PhoneNumberType


class Country(TypedDict):
    id: str
    isoCode: NotRequired[str]
    name: NotRequired[str]


class Address(TypedDict):
    auditId: str
    id: str
    department: NotRequired[str]
    streetName: NotRequired[str]
    houseNumber: NotRequired[str]
    houseNumberSuffix: NotRequired[str]
    city: NotRequired[str]
    postalCode: NotRequired[str]
    province: NotRequired[str]
    country: Country
    customCountryIso: NotRequired[str]


class Location(TypedDict):
    auditId: str
    id: str
    isActive: NotRequired[bool]
    code: NotRequired[str]
    phoneNumberList: NotRequired[list[LocationPhoneNumber]]
    description: NotRequired[str]
    address: Address
    # not listed as optional in the documentation, but none of the example locations
    # include it
    synergyId: NotRequired[str]
    emailAddress: NotRequired[str]
    isDefault: bool
    smtpFromEmailAddress: NotRequired[str]
    smtpFromName: NotRequired[str]
    internetAppointmentBaseUrl: NotRequired[str]
    locationNumber: NotRequired[int]  # will be fully replaced by id eventually


class NoServiceConfigured(RuntimeError):
    pass


@contextmanager
def log_api_errors(event: str):
    try:
        yield
    except requests.RequestException as exc:
        content = exc.response.json() if exc.response is not None else None
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

    def get_activity_list_for_appointment(
        self, location_id: str
    ) -> Collection[Activity]:
        """Get a list of available activities for an appointment."""
        params = [("locationId", location_id)] if location_id else []

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_additional_activity_list_for_appointment(
        self, activity_ids: Collection[str], location_id: str
    ) -> Collection[Activity]:
        """Get a list of additional activities based on selected activities."""
        params: list[tuple[str, str | bool]] = (
            [("locationId", location_id)] if location_id else []
        )
        # Note passing the same query parameter multiple times is intended behavior
        params.extend([("selectedActivityId", id_) for id_ in activity_ids])
        params.append(("includeSelectedActivities", False))

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment/additional", params=params)
            response.raise_for_status()

        return response.json()

    def get_location_list(self) -> Collection[Location]:
        """Get list of locations."""
        with log_api_errors("locations_retrieval_failure"):
            response = self.get("location")
            response.raise_for_status()

        return response.json()

    def get_location_list_for_appointment(
        self, activity_ids: Collection[str]
    ) -> Collection[Location]:
        """
        Get list of locations available for appointment based on selected activities.
        """
        params = [("selectedActivityId", id_) for id_ in activity_ids]
        with log_api_errors("locations_retrieval_failure"):
            response = self.get("location/forappointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_appointment_date_range_for_activities(
        self, activity_ids: Collection[str]
    ) -> tuple[date, date]:
        """
        Get the available date range for an appointment based on provided activities.
        """
        params = [("activityId", id_) for id_ in activity_ids]
        with log_api_errors("date_range_retrieval_failure"):
            response = self.get("activity/appointmentdaterange", params=params)
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
        activity_ids: Sequence[str],
        amounts: Sequence[int],
    ) -> Sequence[datetime]:
        """Get a list of available times for an appointment."""
        assert len(activity_ids) == len(amounts), (
            "Number of activity IDs and amounts must be equal"
        )
        params: list[tuple[str, str | int]] = [
            ("locationId", location_id),
            ("fromDate", from_date.isoformat()),
            ("toDate", to_date.isoformat()),
        ]
        for id_, amount in zip(activity_ids, amounts, strict=True):
            params.append(("activityId", id_))
            params.append(("amount", amount))

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
