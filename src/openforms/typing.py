from typing import TYPE_CHECKING, Any, Dict, List, NewType, Protocol, Union

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from rest_framework.request import Request

if TYPE_CHECKING:
    import datetime
    import decimal
    import uuid

    from django.utils.functional import Promise

JSONPrimitive = Union[str, int, None, float, bool]

JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]

JSONObject = Dict[str, JSONValue]

DataMapping = Dict[str, Any]  # key: value pair

AnyRequest = Union[HttpRequest, Request]

RegistrationBackendKey = NewType("RegistrationBackendKey", str)


class RequestHandler(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponseBase:  # pragma: no cover
        ...


# Types that `django.core.serializers.json.DjangoJSONEncoder` can handle
DjangoJSONEncodable = Union[
    JSONValue,
    "datetime.datetime",
    "datetime.date",
    "datetime.time",
    "datetime.timedelta",
    "decimal.Decimal",
    "uuid.UUID",
    "Promise",
]


class JSONSerializable(Protocol):
    def __json__(self) -> DjangoJSONEncodable:
        ...


JSONEncodable = DjangoJSONEncodable | JSONSerializable
