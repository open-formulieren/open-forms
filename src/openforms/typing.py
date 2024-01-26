import datetime
import decimal
import uuid
from typing import Any, NewType, Protocol, TypeAlias

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.utils.functional import Promise

from rest_framework.request import Request

JSONPrimitive: TypeAlias = str | int | float | bool | None

JSONValue: TypeAlias = "JSONPrimitive | JSONObject | list[JSONValue]"

JSONObject: TypeAlias = dict[str, JSONValue]

DataMapping: TypeAlias = dict[str, Any]  # key: value pair

AnyRequest: TypeAlias = HttpRequest | Request

RegistrationBackendKey = NewType("RegistrationBackendKey", str)


class RequestHandler(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        ...


# Types that `django.core.serializers.json.DjangoJSONEncoder` can handle
DjangoJSONEncodable: TypeAlias = "JSONValue | datetime.datetime | datetime.date | datetime.time | datetime.timedelta | decimal.Decimal | uuid.UUID | Promise"


class JSONSerializable(Protocol):
    def __json__(self) -> DjangoJSONEncodable:
        ...


JSONEncodable: TypeAlias = "DjangoJSONEncodable | JSONSerializable"
