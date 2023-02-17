from typing import Any, Dict, List, Protocol, Union

from django.http import HttpRequest
from django.http.response import HttpResponseBase

JSONPrimitive = Union[str, int, None, float, bool]

JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]

JSONObject = Dict[str, JSONValue]

DataMapping = Dict[str, Any]  # key: value pair


class RequestHandler(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponseBase:  # pragma: no cover
        ...
