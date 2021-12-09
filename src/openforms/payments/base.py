from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from django.http import HttpRequest, HttpResponse

from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import PaymentRequestType

if TYPE_CHECKING:  # pragma: nocover
    from openforms.forms.models import Form

    from .models import Submission, SubmissionPayment


@dataclass()
class APIInfo:
    identifier: str
    label: str


@dataclass()
class PaymentInfo:
    type: str = PaymentRequestType.get
    url: str = ""
    data: Mapping[str, str] = None


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class BasePlugin(AbstractBasePlugin):
    return_method = "GET"
    webhook_method = "POST"
    configuration_options = EmptyOptions

    # override

    def start_payment(
        self,
        request: HttpRequest,
        payment: "SubmissionPayment",
    ) -> PaymentInfo:
        raise NotImplementedError()

    def handle_return(
        self, request: HttpRequest, payment: "SubmissionPayment"
    ) -> HttpResponse:
        raise NotImplementedError()

    def handle_webhook(self, request: HttpRequest) -> "SubmissionPayment":
        raise NotImplementedError()

    # helpers

    def get_start_url(self, request: HttpRequest, submission: "Submission") -> str:
        return reverse(
            "payments:start",
            kwargs={"uuid": submission.uuid, "plugin_id": self.identifier},
            request=request,
        )

    def get_return_url(self, request: HttpRequest, payment: "SubmissionPayment") -> str:
        return reverse(
            "payments:return",
            kwargs={"uuid": payment.uuid},
            request=request,
        )

    def get_webhook_url(self, request: HttpRequest) -> str:
        return reverse(
            "payments:webhook",
            kwargs={"plugin_id": self.identifier},
            request=request,
        )

    def get_api_info(self, request: HttpRequest, form: "Form") -> APIInfo:
        info = APIInfo(
            self.identifier,
            self.get_label(),
        )
        return info
