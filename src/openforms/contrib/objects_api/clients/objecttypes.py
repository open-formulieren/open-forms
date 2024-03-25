from typing import Any
from uuid import UUID

from zgw_consumers.nlx import NLXClient

from openforms.utils.api_clients import PaginatedResponseData, pagination_helper


class ObjecttypesClient(NLXClient):

    def _get_paginated(
        self,
        endpoint: str,
        page: int | None = None,
        page_size: int | None = None,
        query_params: dict[Any, Any] | None = None,
    ):
        query_params = query_params or {}
        if page is None and page_size is None:
            response = self.get(endpoint, params=query_params)
            response.raise_for_status()
            data: PaginatedResponseData[dict[str, Any]] = response.json()
            all_data = pagination_helper(self, data)
            return list(all_data)

        if page is not None:
            query_params["page"] = page
        if page_size is not None:
            query_params["pageSize"] = page_size

        response = self.get(endpoint, params=query_params)
        response.raise_for_status()
        return response.json()["results"]

    def list_objecttypes(
        self,
        page: int | None = None,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        return self._get_paginated(
            "objecttypes",
            page=page,
            page_size=page_size,
        )

    def get_objecttype(
        self,
        objecttype_uuid: str | UUID,
    ) -> dict[str, Any]:
        response = self.get(f"objecttypes/{objecttype_uuid}")
        response.raise_for_status()
        return response.json()

    def list_objecttype_versions(
        self,
        objecttype_uuid: str | UUID,
        page: int | None = None,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        return self._get_paginated(
            f"objecttypes/{objecttype_uuid}/versions", page=page, page_size=page_size
        )

    def get_objecttype_version(
        self,
        objecttype_uuid: str | UUID,
        version: int,
    ) -> dict[str, Any]:
        response = self.get(f"objecttypes/{objecttype_uuid}/versions/{version}")
        response.raise_for_status()
        return response.json()
