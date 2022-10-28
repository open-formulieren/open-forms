from typing import Any, Optional

from zgw_consumers.client import ZGWClient

from .registry import register as registry


class PreRequestZGWClient(ZGWClient):
    _submission = None

    def pre_request(
        self, method: str, url: str, kwargs: Optional[dict] = None
    ) -> Any:
        result = super().pre_request(method, url, kwargs)

        for pre_request in registry:
            pre_request(self._submission, method, url, kwargs)

        return result
