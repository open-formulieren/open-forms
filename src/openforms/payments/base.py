from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from django.http import HttpRequest, HttpResponse

from rest_framework import serializers
from rest_framework.request import Request

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.urls import reverse_plus

from .constants import PaymentRequestType

if TYPE_CHECKING:
    from .models import Submission, SubmissionPayment


@dataclass()
class APIInfo:
    identifier: str
    label: str


@dataclass()
class PaymentInfo:
    type: str = PaymentRequestType.get
    url: str = ""
    data: Mapping[str, str] | None = None


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class Options(TypedDict):
    pass


class BasePlugin[OptionsT: Options](AbstractBasePlugin):
    return_method = "GET"
    webhook_method = "POST"
    configuration_options: type[serializers.Serializer] = EmptyOptions

    # override

    def start_payment(
        self,
        request: HttpRequest,
        payment: SubmissionPayment,
        options: OptionsT,
    ) -> PaymentInfo:
        raise NotImplementedError()

    def handle_return(
        self,
        request: Request,
        payment: SubmissionPayment,
        options: OptionsT,
    ) -> HttpResponse:
        raise NotImplementedError()

    def handle_webhook(self, request: Request) -> SubmissionPayment:
        raise NotImplementedError()

    # helpers

    def get_start_url(self, request: HttpRequest, submission: Submission) -> str:
        return reverse_plus(
            "payments:start",
            kwargs={"uuid": submission.uuid, "plugin_id": self.identifier},
            request=request,
        )

    def get_return_url(self, request: HttpRequest, payment: SubmissionPayment) -> str:
        return reverse_plus(
            "payments:return",
            kwargs={"uuid": payment.uuid},
            request=request,
        )

    def get_webhook_url(self, request: HttpRequest | None) -> str:
        return reverse_plus(
            "payments:webhook",
            kwargs={"plugin_id": self.identifier},
            request=request,
        )

    def get_api_info(self, request: HttpRequest) -> APIInfo:
        info = APIInfo(self.identifier, str(self.get_label()))
        return info
