from typing import TypedDict

from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.tokens import submission_status_token_generator

from ...base import BasePlugin, PaymentInfo
from ...constants import PaymentStatus, UserAction
from ...registry import register


class NoOptions(TypedDict):
    pass


@register("demo")
class DemoPayment(BasePlugin[NoOptions]):
    verbose_name = _("Demo")
    is_demo_plugin = True

    def start_payment(self, request, payment, options):
        url = self.get_return_url(request, payment)
        return PaymentInfo(url=url, data={})

    def handle_return(self, request, payment, options):
        payment.status = PaymentStatus.completed
        payment.save()

        submission = payment.submission
        token = submission_status_token_generator.make_token(submission)
        status_url = request.build_absolute_uri(
            reverse(
                "api:submission-status",
                kwargs={"uuid": submission.uuid, "token": token},
            )
        )

        redirect_url = get_frontend_redirect_url(
            submission,
            action="payment",
            action_params={
                "of_payment_status": payment.status,
                "of_payment_id": str(payment.uuid),
                "of_payment_action": UserAction.accept,
                "of_submission_status": status_url,
            },
        )
        return HttpResponseRedirect(redirect_url)

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
