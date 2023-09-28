from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from requests.models import PreparedRequest, Request

from .registry import register as registry

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class PreRequestClientContext(TypedDict):
    submission: Submission | None


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

        return super().prepare_request(request)  # type: ignore
