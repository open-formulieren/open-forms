from zds_client.schema import get_operation_url
from zgw_consumers.client import ZGWClient

from api_client import APIClient

HAL_CONTENT_TYPE = "application/hal+json"


class HALMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Accept": HAL_CONTENT_TYPE,
                "Content-Type": HAL_CONTENT_TYPE,
            }
        )


class HALClient(HALMixin, APIClient):
    pass


# deprecated
class HalClient(ZGWClient):
    def pre_request(self, method, url, kwargs):
        """
        Add authorization header to requests for APIs without jwt.
        """

        result = super().pre_request(method, url, kwargs)

        headers = kwargs.get("headers", {})
        headers["Accept"] = "application/hal+json"
        headers["Content-Type"] = "application/hal+json"
        return result

    def get_operation_url(self, operation_id: str, **path_kwargs):
        return get_operation_url(
            self.schema, operation_id, base_url=self.api_root, **path_kwargs
        )
