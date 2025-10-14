from collections.abc import Collection, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from typing import TypedDict

from django.utils.translation import get_language

import requests
import structlog
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingClient

from .exceptions import GracefulJccRestException, JccRestException
from .models import JccRestConfig

logger = structlog.stdlib.get_logger(__name__)


# Source for the typed dict definitions:
# https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
class Activity(TypedDict):
    id: str
    number: int
    code: str | None
    description: str | None
    necessities: str | None
    appointmentDuration: int
    maxCountForEvent: int | None
    activityGroupId: str | None
    synonyms: list[str] | None


class Revision(TypedDict):
    id: str
    creationDateTime: str
    creatorAuthenticationUserId: str | None


class PhoneNumber(TypedDict):
    auditId: str
    id: str
    revision: Revision
    value: str | None


class PhoneNumberType(TypedDict):
    auditId: str
    id: str
    revision: Revision
    name: str | None
    description: str | None


class LocationPhoneNumber(TypedDict):
    auditId: str
    id: str
    revision: Revision
    phoneNumber: PhoneNumber
    phoneNumberType: PhoneNumberType


class Country(TypedDict):
    id: str
    isoCode: str | None
    name: str | None


class Address(TypedDict):
    auditId: str
    id: str
    revision: Revision
    department: str | None
    streetName: str | None
    houseNumber: str | None
    houseNumberSuffix: str | None
    city: str | None
    postalCode: str | None
    city: str | None
    province: str | None
    country: Country
    customCountryIso: str | None


class Location(TypedDict):
    auditId: str
    id: str
    revision: Revision
    isActive: bool | None
    code: str | None
    phoneNumberList: list[LocationPhoneNumber] | None
    description: str | None
    address: Address
    synergyId: str | None
    emailAddress: str | None
    isDefault: bool
    smtpFromEmailAddress: str | None
    smtpFromName: str | None
    internetAppointmentBaseUrl: str | None
    locationNumber: str | None


class NoServiceConfigured(RuntimeError):
    pass


# TODO-5696: we might be able to include the error message from the response
@contextmanager
def log_api_errors(event: str):
    try:
        yield
    except requests.RequestException as exc:
        logger.exception(event, exc_info=exc)
        raise GracefulJccRestException("JCC REST API call failed") from exc
    except Exception as exc:
        raise JccRestException from exc


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

    def get_activity_list_for_appointment(
        self, location_id: str
    ) -> Collection[Activity]:
        params = [("locationId", location_id)] if location_id else []

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_additional_activity_list_for_appointment(
        self, activity_ids: Collection[str], location_id: str
    ) -> Collection[Activity]:
        params: list[tuple[str, str | bool]] = (
            [("locationId", location_id)] if location_id else []
        )
        # Note passing the same query parameter multiple times is intended behaviour
        params.extend([("selectedActivityId", id_) for id_ in activity_ids])
        params.append(("includeSelectedActivities", False))

        with log_api_errors("activities_retrieval_failure"):
            response = self.get("activity/listforappointment/additional", params=params)
            response.raise_for_status()

        return response.json()

    def get_location_list(self) -> Collection[Location]:
        with log_api_errors("locations_retrieval_failure"):
            response = self.get("location")
            response.raise_for_status()

        return response.json()

    def get_location_list_for_appointment(
        self, activity_ids: Collection[str]
    ) -> Collection[Location]:
        params = [("selectedActivityId", id_) for id_ in activity_ids]
        with log_api_errors("locations_retrieval_failure"):
            response = self.get("location/forappointment", params=params)
            response.raise_for_status()

        return response.json()

    def get_appointment_date_range_for_activities(
        self, activity_ids: Collection[str]
    ) -> tuple[date, date]:
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
    ) -> list[datetime]:
        assert len(activity_ids) == len(amounts), (
            "Number of activity IDs and amounts must be equal"
        )
        params: list[tuple[str, str | int]] = [
            ("locationId", location_id),
            ("fromDate", from_date.isoformat()),
            ("toDate", to_date.isoformat()),
        ]
        for id_, amount in zip(activity_ids, amounts, strict=False):
            params.append(("activityId", id_))
            params.append(("amount", amount))

        with log_api_errors("available_times_retrieval_failure"):
            response = self.get("appointment/availabletimelist", params=params)
            response.raise_for_status()

        return sorted(
            {
                datetime.fromisoformat(date_string)
                for date_string in response.json()["availableTimesList"]
            }
        )
