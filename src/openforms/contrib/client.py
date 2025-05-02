from typing import TYPE_CHECKING

import structlog
from ape_pie import APIClient

if TYPE_CHECKING:
    Base = APIClient
else:
    Base = object


class LoggingMixin(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        structlog.contextvars.bind_contextvars(base_url=self.base_url, client=self)

    def request(self, method: str | bytes, url: str | bytes, *args, **kwargs):
        structlog.contextvars.bind_contextvars(method=method, endpoint=url)
        return super().request(method, url, *args, **kwargs)

    def __exit__(self, *args):
        structlog.contextvars.unbind_contextvars(
            "base_url", "client", "method", "endpoint"
        )
        return super().__exit__(self, *args)


class LoggingClient(LoggingMixin, APIClient):
    pass
