from requests import Session

from .models import QmaticConfig


class QmaticException(Exception):
    pass


class QmaticClient(Session):
    """
    Lightweight wrapper around Session to work with the API root and auth
    headers.
    """

    _config = None

    def request(self, method: str, url: str, *args, **kwargs):
        if not self._config:
            self._config = QmaticConfig.get_solo()

        api_root = self._config.service.api_root
        headers = {
            "Content-Type": "application/json",
        }
        headers.update(self._config.service.get_auth_header(api_root))

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
