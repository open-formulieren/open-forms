from requests import Session

from .models import QmaticConfig


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
        headers = self._config.service.get_auth_header(api_root)

        url = f"{api_root}{url}"
        return super().request(method, url, headers=headers, *args, **kwargs)
