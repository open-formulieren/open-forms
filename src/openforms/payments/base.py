from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

if TYPE_CHECKING:
    from openforms.forms.models import Form


@dataclass()
class APIInfo:
    identifier: str
    label: str


class BasePlugin:
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    """
    Specify the human-readable label for the plugin.
    """
    return_method = "GET"

    def __init__(self, identifier: str):
        self.identifier = identifier

    # override

    def start_payment(
        self,
        request: HttpRequest,
        submission: "Submission",
        form_url: str,
        payment_amount: Decimal,
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()

    def handle_return(
        self, request: HttpRequest, submission: "Submission"
    ) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()

    # helpers

    def get_start_url(self, request: HttpRequest, submission: "Submission") -> str:
        return reverse(
            "payments:start",
            kwargs={"uuid": submission.uuid, "plugin_id": self.identifier},
            request=request,
        )

    def get_return_url(self, request: HttpRequest, submission: "Submission") -> str:
        return reverse(
            "payments:return",
            kwargs={"uuid": submission.uuid, "plugin_id": self.identifier},
            request=request,
        )

    def get_api_info(self, request: HttpRequest, submission: "Submission") -> APIInfo:
        info = APIInfo(
            self.identifier,
            self.get_label(),
        )
        return info

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name
