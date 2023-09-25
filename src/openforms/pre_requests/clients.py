from typing import TYPE_CHECKING, Any, Optional, TypedDict

from requests.models import PreparedRequest, Request
from zgw_consumers.client import ZGWClient

from .registry import register as registry

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class PreRequestClientContext(TypedDict):
    submission: Optional["Submission"]


class PreRequestZGWClient(ZGWClient):
    """
    A :class:`zgw_consumers.client.ZGWClient` with pre-requests support.

    .. note:: this client is being deprecated in favour of a pure requests approach,
       using :class:`api_client.APIClient`
    """

    _context = None

    def pre_request(self, method: str, url: str, kwargs: Optional[dict] = None) -> Any:
        result = super().pre_request(method, url, kwargs)

        for pre_request in registry:
            pre_request(method, url, kwargs, context=self._context)

        return result

    @property
    def context(self) -> Optional[PreRequestClientContext]:
        return self._context

    @context.setter
    def context(self, context: PreRequestClientContext) -> None:
        self._context = context


KNOWN_REQUEST_KWARG_ATTRIBUTES = (
    "params",
    "data",
    "json",
    "headers",
    "cookies",
    "files",
    "auth",
    "hooks",
)


def request_as_kwargs(request: Request) -> dict[str, Any]:
    return {kwarg: getattr(request, kwarg) for kwarg in KNOWN_REQUEST_KWARG_ATTRIBUTES}


class PreRequestMixin:
    """
    Mix in pre-requests support for :class:`requests.Session`-based classes/clients.

    TODO: update mechanism so the hooks receive the full ``request`` instance rather
    than just some aspects of it.
    """

    def __init__(self, *args, context: PreRequestClientContext | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pre_request_context = context

    def prepare_request(self, request: Request) -> PreparedRequest:
        method = request.method.upper()
        url = request.url
        kwargs = request_as_kwargs(request)

        for pre_request in registry:
            pre_request(method, url, kwargs, context=self.pre_request_context)

        # assign the kwargs again so any middleware is applied to the request
        for key, value in kwargs.items():
            setattr(request, key, value)

        return super().prepare_request(request)
