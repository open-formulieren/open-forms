from datetime import date, datetime, time
from typing import TypedDict
from zoneinfo import ZoneInfo

from ape_pie.client import APIClient
from dateutil.parser import isoparse
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from .exceptions import QmaticException
from .models import QmaticConfig

# API DATA DEFINITIONS


class ServiceDict(TypedDict):
    publicId: str
    name: str
    # could be float too in theory, documentation is not specific (it gives an int example)
    duration: int
    additionalCustomerDuration: int
    custom: str | None


class FullServiceDict(ServiceDict):
    active: bool
    publicEnabled: bool
    created: int
    updated: int


class ServiceGroupDict(TypedDict):
    services: list[ServiceDict]


class BranchDict(TypedDict):
    branchPublicId: str
    branchName: str
    serviceGroups: list[ServiceGroupDict]


class BranchDetailDict(TypedDict):
    name: str
    publicId: str
    phone: str
    email: str
    branchPrefix: str | None

    addressLine1: str | None
    addressLine2: str | None
    addressZip: str | None
    addressCity: str | None
    addressState: str | None
    addressCountry: str | None

    latitude: float | None
    longitude: float | None
    timeZone: str
    fullTimeZone: str
    custom: str | None
    created: int
    updated: int


class NoServiceConfigured(RuntimeError):
    pass


# API CLIENT IMPLEMENTATIONS, per major version of the API


def QmaticClient() -> "Client":
    """
    Create a Qmatic client instance from the database configuration.
    """
    config = QmaticConfig.get_solo()
    if (service := config.service) is None:
        raise NoServiceConfigured("No Qmatic service defined, aborting!")
    assert isinstance(service, Service)
    return build_client(service, client_factory=Client)


def startswith_version(url: str) -> bool:
    if url.startswith("v1/"):
        return True
    if url.startswith("v2/"):
        return True
    return False


class Client(APIClient):
    """
    Client implementation for Qmatic.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["Content-Type"] = "application/json"

    def request(self, method: str, url: str, *args, **kwargs):
        # ensure there is a version identifier in the URL
        if not startswith_version(url):
            url = f"v1/{url}"

        response = super().request(method, url, *args, **kwargs)

        if response.status_code == 500:
            error_msg = response.headers.get(
                "error_message", response.content.decode("utf-8")
            )
            raise QmaticException(
                f"Server error (HTTP {response.status_code}): {error_msg}"
            )

        return response

    def list_services(self, location_id: str = "") -> list[FullServiceDict]:
        endpoint = f"branches/{location_id}/services" if location_id else "services"
        response = self.get(endpoint)
        response.raise_for_status()
        return response.json()["serviceList"]

    def list_service_groups(
        self, service_ids: list[str], location_id: str = ""
    ) -> list[ServiceGroupDict]:
        assert service_ids, "Unexpectedly received an empty list of service IDs"
        params = ";".join(
            [f"servicePublicId={service_id}" for service_id in service_ids]
        )
        endpoint = (
            (f"v2/branches/{location_id}/services/groups;{params}")
            if location_id
            else (f"v1/services/groups;{params}")
        )
        response = self.get(endpoint)
        response.raise_for_status()

        # the shape depends on whether we hit v1 or v2
        response_data = response.json()

        # v2 API returns a list of service groups (expected to only have one item)
        if location_id:
            return response_data

        # v1 API returns a list of branches
        branches: list[BranchDict] = response_data
        service_groups = sum((branch["serviceGroups"] for branch in branches), [])
        return service_groups

    def get_branch(self, branch_id: str) -> BranchDetailDict:
        response = self.get(f"v1/branches/{branch_id}")
        response.raise_for_status()
        branch: BranchDetailDict = response.json()["branch"]
        return branch

    def list_dates(
        self, location_id: str, service_ids: list[str], num_customers: int
    ) -> list[date]:
        """
        Get list of available dates for multiple services and customers.

        ``num_customers`` is the total number of customers, which affects the
        appointment duration in Qmatic (using
        ``duration + additionalCustomerDuration * numAdditionalCustomers``, where
        ``numAdditionalCustomers`` is ``numCustomers - 1``.
        ).

        Note that Qmatic returns a list of datetimes without timezone information.
        """
        assert location_id, "Unexpectedly received empty location ID"
        assert service_ids, "Unexpectedly received an empty list of service IDs"
        assert num_customers > 0, "Need at least one customer"

        params = [f"servicePublicId={service_id}" for service_id in service_ids]
        if num_customers > 1:
            params += [f"numberOfCustomers={num_customers - 1}"]
        serializedParams = ";".join(params)

        # get the branch detail so we can interpret the timezone correctly
        branch = self.get_branch(location_id)
        branch_timezone = ZoneInfo(branch["timeZone"])

        # get the dates
        endpoint = f"v2/branches/{location_id}/dates;{serializedParams}"
        response = self.get(endpoint)
        response.raise_for_status()

        dates: list[date] = [
            isoparse(value).replace(tzinfo=branch_timezone).date()
            for value in response.json()["dates"]
        ]
        return dates

    def list_times(
        self, location_id: str, service_ids: list[str], day: date, num_customers: int
    ) -> list[datetime]:
        """
        Get list of available times for multiple services and customers.

        ``num_customers`` is the total number of customers, which affects the
        appointment duration in Qmatic (using
        ``duration + additionalCustomerDuration * numAdditionalCustomers``, where
        ``numAdditionalCustomers`` is ``numCustomers - 1``.
        ).

        Note that Qmatic returns a list of datetimes without timezone information.
        """
        assert location_id, "Unexpectedly received empty location ID"
        assert service_ids, "Unexpectedly received an empty list of service IDs"
        assert num_customers > 0, "Need at least one customer"

        params = [f"servicePublicId={service_id}" for service_id in service_ids]
        if num_customers > 1:
            params += [f"numberOfCustomers={num_customers - 1}"]
        serializedParams = ";".join(params)

        # get the branch detail so we can correctly apply the timezone
        branch = self.get_branch(location_id)
        branch_timezone = ZoneInfo(branch["timeZone"])

        # get the times
        endpoint = f"v2/branches/{location_id}/dates/{day.isoformat()}/times;{serializedParams}"
        response = self.get(endpoint)
        response.raise_for_status()

        datetimes = [
            datetime.combine(day, time.fromisoformat(entry)).astimezone(branch_timezone)
            for entry in response.json()["times"]
        ]
        return datetimes
