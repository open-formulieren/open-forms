from __future__ import annotations

import datetime
import decimal
import uuid
from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, NewType, Protocol

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.utils.functional import Promise

from dateutil.relativedelta import relativedelta
from rest_framework.request import Request
from typing_extensions import TypeIs

if TYPE_CHECKING:
    from django.utils.functional import _StrOrPromise

    from openforms.accounts.models import User
else:
    _StrOrPromise = str

type JSONPrimitive = str | int | float | bool | None

type JSONValue = JSONPrimitive | JSONObject | Sequence[JSONValue]

type JSONObject = MutableMapping[str, JSONValue]

type DataMapping = MutableMapping[str, Any]  # key: value pair

type AnyRequest = HttpRequest | Request

RegistrationBackendKey = NewType("RegistrationBackendKey", str)

type StrOrPromise = _StrOrPromise
"""Either ``str`` or a ``Promise`` object returned by the lazy ``gettext`` functions."""


class RequestHandler(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponseBase: ...


# Types that `django.core.serializers.json.DjangoJSONEncoder` can handle
type DjangoJSONEncodable = (
    JSONValue
    | datetime.datetime
    | datetime.date
    | datetime.time
    | datetime.timedelta
    | decimal.Decimal
    | uuid.UUID
    | Promise
)


class JSONSerializable(Protocol):
    def __json__(self) -> DjangoJSONEncodable: ...


type JSONEncodable = DjangoJSONEncodable | JSONSerializable

type VariableValue = (
    JSONValue
    | datetime.date
    | datetime.time
    | datetime.datetime
    | relativedelta
    | list[VariableValue]  # for components configured as multiple
    | dict[str, VariableValue]
)


class AuthenticatedHttpRequest(HttpRequest):
    user: User  # pyright: ignore[reportIncompatibleVariableOverride]


def is_authenticated_request(request: HttpRequest) -> TypeIs[AuthenticatedHttpRequest]:
    return request.user.is_authenticated
