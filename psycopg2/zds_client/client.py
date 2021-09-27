import copy
import logging
import re
import warnings
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
import yaml
from requests.structures import CaseInsensitiveDict

from .config import ClientConfig
from .log import Log
from .oas import schema_fetcher
from .registry import registry
from .schema import get_headers, get_operation_url

logger = logging.getLogger(__name__)

Object = Dict[str, Any]

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}",
    flags=re.I,
)


class ClientError(Exception):
    pass


class Client:

    _schema = None
    _log = Log()

    auth = None

    operation_suffix_mapping = {
        "list": "_list",
        "retrieve": "_read",
        "create": "_create",
        "update": "_update",
        "partial_update": "_partial_update",
        "delete": "_delete",
    }

    def __init__(self, service: str, base_path: str = "/api/v1/"):
        """
        Obtain a client instance from the configuration registry.

        :param service: Alias of the service/API
        """
        try:
            self._config = registry[service]
        except KeyError:
            raise RuntimeError(
                "Service '{service}' is not known in the client registry. "
                "Did you load the config first through `Client.load_config(path, **manual)`?".format(
                    service=service
                )
            )

        self.service = service
        self.base_path = base_path

        self._base_url = None

        self.auth = self._config.auth

    def __repr__(self):
        return "<%s: service=%r base_url=%r>" % (
            self.__class__.__name__,
            self.service,
            self.base_url,
        )

    @classmethod
    def load_config(cls, path: str = None, **manual):
        """
        Initialize the client configuration.

        The configuration is delegated to the registry, so multiple instances
        of the client share the same configuration.

        The config file should have the following format:

        .. code-block:: yaml

            alias1:
              scheme: http(s)
              host: localhost
              port: 8000
              auth:
                client_id: some-client-id
                secret: very-secret

        Multiple service configs are supported, each with their own alias.
        The `port` and `auth` keys are optional. Port will default to 80 or
        443 depending on the scheme.

        :param path: path to the yaml file holding the config
        :param manual: any manual overrides, as kwargs. Note this completely
          overwrites any existing config in the YAML file if specified.
        """
        if path is not None:
            logger.info("Loading config from %s", path)
            with open(path, "r") as config_file:
                client_configs = yaml.safe_load(config_file)

            for alias, _config in client_configs.items():
                config = ClientConfig.from_dict(_config)
                registry.register(alias, config)

        if manual:
            logger.info("Applying manual config: %r", manual)
            for alias, _config in manual.items():
                config = ClientConfig.from_dict(_config)
                registry.register(alias, config)

    @classmethod
    def from_url(cls, detail_url: str) -> "Client":
        parsed_url = urlparse(detail_url)

        # we know that API endpoints look like:
        # - /base_path/collection/<uuid> or
        # - /base_path/collection/<uuid>/subcollection or
        # - /base_path/collection/<uuid>/subcollection/<uuid>
        # So, splitting on UUIDs gives us the base_path + collection
        bits = re.split(UUID_PATTERN, parsed_url.path)
        base_path = (bits[0].rstrip("/").rsplit("/", 1))[0] + "/"

        # register the config
        config = ClientConfig.from_url(detail_url)
        alias = config.base_url
        registry.register(alias, config)
        return cls(alias, base_path)

    @property
    def log(self):
        """
        Local log entries.
        """
        return (
            entry for entry in self._log.entries() if entry["service"] == self.service
        )

    @property
    def base_url(self) -> str:
        default = f"{self._config.base_url}{self.base_path}"
        return self._base_url or default

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        self._base_url = base_url

    @property
    def schema(self):
        if self._schema is None:
            self.fetch_schema()
        return self._schema

    def pre_request(self, method: str, url: str, **kwargs) -> Any:
        """
        Perform any pre-request processing required.

        The kwargs are literally passed to :meth:`requests.request` and may
        be mutated in place.

        The return value is passed as first argument to :meth:`post_response`.
        """
        pass

    def request(
        self,
        path: str,
        operation: str,
        method="GET",
        expected_status=200,
        request_kwargs: Optional[dict] = None,
        **kwargs,
    ) -> Union[List[Object], Object]:
        """
        Make the HTTP request using requests.

        The URL is created based on the path and base URL and any defaults
        from the OAS schema are injected.

        :return: a list or dict, the result of calling response.json()
        :raises: :class:`requests.HTTPException` for internal server errors
        :raises: :class:`ClientError` for HTTP 4xx status codes
        """
        url = urljoin(self.base_url, path)

        if request_kwargs:
            kwargs.update(request_kwargs)

        headers = CaseInsensitiveDict(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Content-Type", "application/json")
        schema_headers = get_headers(self.schema, operation)
        for header, value in schema_headers.items():
            headers.setdefault(header, value)
        if self.auth:
            headers.update(self.auth.credentials())

        kwargs["headers"] = headers

        pre_id = self.pre_request(method, url, **kwargs)

        response = requests.request(method, url, **kwargs)

        try:
            response_json = response.json()
        except Exception:
            response_json = None

        self.post_response(pre_id, response_json)

        self._log.add(
            self.service,
            url,
            method,
            dict(headers),
            copy.deepcopy(kwargs.get("data", kwargs.get("json", None))),
            response.status_code,
            dict(response.headers),
            response_json,
            params=kwargs.get("params"),
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if response.status_code >= 500:
                raise
            raise ClientError(response_json) from exc

        assert response.status_code == expected_status, response_json
        return response_json

    def post_response(
        self, pre_id: Any, response_data: Optional[Union[dict, list]] = None
    ) -> None:
        pass

    def fetch_schema(self) -> None:
        url = urljoin(self.base_url, "schema/openapi.yaml")
        logger.info("Fetching schema at '%s'", url)
        self._schema = schema_fetcher.fetch(url, {"v": "3"})

    def list(
        self,
        resource: str,
        params=None,
        query_params=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> List[Object]:
        op_suffix = self.operation_suffix_mapping["list"]
        operation_id = f"{resource}{op_suffix}"
        url = get_operation_url(
            self.schema, operation_id, base_url=self.base_url, **path_kwargs
        )
        if query_params and not params:
            warnings.warn(
                "Client.list 'query_params' kwarg is deprecated, use 'params' instead.",
                DeprecationWarning,
            )
            params = query_params

        return self.request(
            url, operation_id, params=params, request_kwargs=request_kwargs
        )

    def retrieve(
        self,
        resource: str,
        url=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Object:
        op_suffix = self.operation_suffix_mapping["retrieve"]
        operation_id = f"{resource}{op_suffix}"
        if url is None:
            url = get_operation_url(
                self.schema, operation_id, base_url=self.base_url, **path_kwargs
            )
        return self.request(url, operation_id, request_kwargs=request_kwargs)

    def create(
        self,
        resource: str,
        data: dict,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Object:
        op_suffix = self.operation_suffix_mapping["create"]
        operation_id = f"{resource}{op_suffix}"
        url = get_operation_url(
            self.schema, operation_id, base_url=self.base_url, **path_kwargs
        )
        return self.request(
            url,
            operation_id,
            method="POST",
            json=data,
            expected_status=201,
            request_kwargs=request_kwargs,
        )

    def update(
        self,
        resource: str,
        data: dict,
        url=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Object:
        op_suffix = self.operation_suffix_mapping["update"]
        operation_id = f"{resource}{op_suffix}"
        if url is None:
            url = get_operation_url(
                self.schema, operation_id, base_url=self.base_url, **path_kwargs
            )
        return self.request(
            url,
            operation_id,
            method="PUT",
            json=data,
            expected_status=200,
            request_kwargs=request_kwargs,
        )

    def partial_update(
        self,
        resource: str,
        data: dict,
        url=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Object:
        op_suffix = self.operation_suffix_mapping["partial_update"]
        operation_id = f"{resource}{op_suffix}"
        if url is None:
            url = get_operation_url(
                self.schema, operation_id, base_url=self.base_url, **path_kwargs
            )
        return self.request(
            url,
            operation_id,
            method="PATCH",
            json=data,
            expected_status=200,
            request_kwargs=request_kwargs,
        )

    def delete(
        self,
        resource: str,
        url=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Object:
        op_suffix = self.operation_suffix_mapping["delete"]
        operation_id = f"{resource}{op_suffix}"
        if url is None:
            url = get_operation_url(
                self.schema, operation_id, base_url=self.base_url, **path_kwargs
            )
        return self.request(
            url,
            operation_id,
            method="DELETE",
            expected_status=204,
            request_kwargs=request_kwargs,
        )

    def operation(
        self,
        operation_id: str,
        data: dict,
        method="POST",
        url=None,
        request_kwargs: Optional[dict] = None,
        **path_kwargs,
    ) -> Union[List[Object], Object]:
        if url is None:
            url = get_operation_url(
                self.schema, operation_id, base_url=self.base_url, **path_kwargs
            )
        return self.request(
            url, operation_id, method=method, json=data, request_kwargs=request_kwargs
        )
