"""
Implements an API client class as a :class:`requests.Session` subclass.

Some inspiration was taken from https://github.com/guillp/requests_oauth2client/,
notably:

* Implementing the client as a ``Session`` subclass
* Providing a base_url and making this absolute
"""
from typing import Any

from furl import furl
from requests import Session

from .exceptions import InvalidURLError
from .typing import APIClientFactory

sentinel = object()


def has_same_base(url: furl, reference: furl) -> bool:
    if not all(
        (
            getattr(url, attr) == getattr(reference, attr)
            for attr in ("scheme", "username", "password", "host", "port")
        )
    ):
        return False
    # finally, if all that is the same, the path base should match too
    return str(url).startswith(str(reference))


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
        url = self.to_absolute_url(url)
        return super().request(method, url, *args, **kwargs)

    def to_absolute_url(self, maybe_relative_url: str) -> str:
        base_furl = furl(self.base_url)
        target_furl = furl(maybe_relative_url)
        is_absolute = target_furl.path.isabsolute
        if is_absolute:
            if not has_same_base(target_furl, base_furl):
                raise InvalidURLError(
                    f"Target URL {maybe_relative_url} has a different base URL than the "
                    f"client ({self.base_url})."
                )
            return maybe_relative_url
        fully_qualified = base_furl / maybe_relative_url
        return str(fully_qualified)
