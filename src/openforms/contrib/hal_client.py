from zds_client.schema import get_operation_url
from zgw_consumers.client import ZGWClient


class HalClient(ZGWClient):
    def pre_request(self, method, url, **kwargs):
        """
        Add authorization header to requests for APIs without jwt.
        """

        result = super().pre_request(method, url, **kwargs)

        headers = kwargs.get("headers", {})
        headers["Accept"] = "application/hal+json"
        headers["Content-Type"] = "application/hal+json"
        return result

    def get_operation_url(self, operation_id: str, **path_kwargs):
        return get_operation_url(
            self.schema, operation_id, base_url=self.base_url, **path_kwargs
        )
