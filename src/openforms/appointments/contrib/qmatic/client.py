from typing import Literal

from requests import Session

from .exceptions import QmaticException
from .models import QmaticConfig


class QmaticClient(Session):
    """
    Lightweight wrapper around Session to work with the API root and auth
    headers.
    """

    _config: QmaticConfig | None = None
    version: Literal["v1", "v2"] = "v1"

    def request(self, method: str, url: str, *args, **kwargs):
        if not self._config:
            config = QmaticConfig.get_solo()
            assert isinstance(config, QmaticConfig)
            self._config = config

        # zgw-consumers normalizes api_root to have a trailing slash
        api_root = f"{self._config.service.api_root}{self.version}/"
        _temp_client = self._config.service.build_client()
        headers = {
            "Content-Type": "application/json",
            **_temp_client.auth_header,
        }
        del _temp_client

        url = f"{api_root}{url}"
        response = super().request(method, url, headers=headers, *args, **kwargs)

        if response.status_code == 500:
            error_msg = response.headers.get(
                "error_message", response.content.decode("utf-8")
            )
            raise QmaticException(
                f"Server error (HTTP {response.status_code}): {error_msg}"
            )

        return response


class QmaticV1Client(QmaticClient):
    version = "v1"


class QmaticV2Client(QmaticClient):
    version = "v2"
