import logging
from typing import Dict, Optional
from urllib.parse import urljoin

from django.utils.module_loading import import_string

from zds_client import Client
from zds_client.oas import schema_fetcher

from .settings import get_setting

logger = logging.getLogger(__name__)


def get_client_class() -> type:
    client_class = get_setting("ZGW_CONSUMERS_CLIENT_CLASS")
    Client = import_string(client_class)
    return Client


class ZGWClient(Client):
    auth_value: Optional[Dict[str, str]] = None
    schema_url: str = ""

    def fetch_schema(self) -> None:
        """ support custom urls for OAS """
        url = self.schema_url or urljoin(self.base_url, "schema/openapi.yaml")
        logger.info("Fetching schema at '%s'", url)
        self._schema = schema_fetcher.fetch(url, {"v": "3"})

    def pre_request(self, method, url, **kwargs):
        """
        Add authorization header to requests for APIs without jwt.
        """
        if not self.auth and self.auth_value:
            headers = kwargs.get("headers", {})
            headers.update(self.auth_value)

        return super().pre_request(method, url, **kwargs)

    @property
    def auth_header(self) -> dict:
        if self.auth:
            return self.auth.credentials()

        return self.auth_value or {}


class UnknownService(Exception):
    pass
