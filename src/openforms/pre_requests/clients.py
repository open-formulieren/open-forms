from typing import Any

from zgw_consumers.client import ZGWClient

from .registry import register as registry


class PreRequestZGWClient(ZGWClient):
    def pre_request(self, method: str, url: str, **kwargs) -> Any:
        result = super().pre_request(method, url, **kwargs)

        for pre_request in registry:
            pre_request(method, url, **kwargs)

        return result
