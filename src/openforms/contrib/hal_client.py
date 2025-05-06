from .client import LoggingClient

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


class HALClient(HALMixin, LoggingClient):
    pass
