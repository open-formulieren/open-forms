from typing import Any

from requests import Session

from .typing import APIClientFactory

sentinel = object()


class APIClient(Session):
    base_url: str
    _request_kwargs: dict[str, Any]

    def __init__(self, base_url: str, request_kwargs: dict[str, Any] | None = None):
        # base class does not take any kwargs
        super().__init__()
        # normalize to dict
        request_kwargs = request_kwargs or {}

        self.base_url = base_url

        # set the attributes that requests.Session supports directly, but only if an
        # actual value was provided.
        for attr in self.__attrs__:
            val = request_kwargs.pop(attr, sentinel)
            if val is sentinel:
                continue
            setattr(self, attr, val)

        # store the remainder so we can inject it in the ``request`` method.
        self._request_kwargs = request_kwargs

    @classmethod
    def configure_from(cls, factory: APIClientFactory):
        base_url = factory.get_client_base_url()
        session_kwargs = factory.get_client_session_kwargs()
        return cls(base_url, session_kwargs)

    def request(self, method, url, *args, **kwargs):
        for attr, val in self._request_kwargs.items():
            kwargs.setdefault(attr, val)

        # TODO: validate that the URL is relative or fits within the self.base_url

        return super().request(method, url, *args, **kwargs)
