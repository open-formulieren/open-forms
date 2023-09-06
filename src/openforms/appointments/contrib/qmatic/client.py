from typing import TypedDict

from requests import Session

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


# API CLIENT IMPLEMENTATIONS, per major version of the API


def startswith_version(url: str) -> bool:
    if url.startswith("v1/"):
        return True
    if url.startswith("v2/"):
        return True
    return False


class QmaticClient(Session):
    """
    Lightweight wrapper around Session to work with the API root and auth
    headers.
    """

    _config: QmaticConfig | None = None

    def request(self, method: str, url: str, *args, **kwargs):
        if not self._config:
            config = QmaticConfig.get_solo()
            assert isinstance(config, QmaticConfig)
            self._config = config

        # ensure there is a version identifier in the URL
        if not startswith_version(url):
            url = f"v1/{url}"

        _temp_client = self._config.service.build_client()
        headers = {
            "Content-Type": "application/json",
            **_temp_client.auth_header,
        }
        del _temp_client

        url = f"{self._config.service.api_root}{url}"
        response = super().request(method, url, headers=headers, *args, **kwargs)

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
