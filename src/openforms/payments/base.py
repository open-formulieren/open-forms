from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import PaymentRequestType

if TYPE_CHECKING:
    from openforms.forms.models import Form
    from openforms.payments.models import SubmissionPayment
    from openforms.submissions.models import Submission


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


class BasePlugin:
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    """
    Specify the human-readable label for the plugin.
    """
    return_method = "GET"
    webhook_method = "POST"
    configuration_options = EmptyOptions
    is_demo_plugin = False

    def __init__(self, identifier: str):
        self.identifier = identifier

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

    def handle_webhook(self, request: HttpRequest) -> None:
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

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name
