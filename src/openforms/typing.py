from typing import Any, Dict, List, NewType, Protocol, Union

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from rest_framework.request import Request

JSONPrimitive = Union[str, int, None, float, bool]

JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]

JSONObject = Dict[str, JSONValue]

DataMapping = Dict[str, Any]  # key: value pair

AnyRequest = Union[HttpRequest, Request]

RegistrationBackendKey = NewType("RegistrationBackendKey", str)


class RequestHandler(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponseBase:  # pragma: no cover
        ...
