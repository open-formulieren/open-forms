from typing import Any, Optional

from zgw_consumers.client import ZGWClient

from .registry import register as registry


class PreRequestZGWClient(ZGWClient):
    def pre_request(
        self, method: str, url: str, kwargs: Optional[dict] = None, **old_kwargs
    ) -> Any:
        result = super().pre_request(method, url, kwargs, **old_kwargs)

        for pre_request in registry:
            pre_request(method, url, kwargs)

        return result
