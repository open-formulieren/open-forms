from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.submissions.tokens import submission_status_token_generator

from ...base import BasePlugin, PaymentInfo
from ...constants import PaymentStatus, UserAction
from ...registry import register


@register("demo")
class DemoPayment(BasePlugin):
    verbose_name = _("Demo")
    is_demo_plugin = True

    def start_payment(self, request, payment):
        url = self.get_return_url(request, payment)
        return PaymentInfo(url=url, data={})

    def handle_return(self, request, payment):
        payment.status = PaymentStatus.completed
        payment.save()

        token = submission_status_token_generator.make_token(payment.submission)
        status_url = request.build_absolute_uri(
            reverse(
                "api:submission-status",
                kwargs={"uuid": payment.submission.uuid, "token": token},
            )
        )

        form_url = payment.submission.cleaned_form_url
        form_url.args.update(
            {
                "of_payment_status": payment.status,
                "of_payment_id": str(payment.uuid),
                "of_payment_action": UserAction.accept,
                "of_submission_status": status_url,
            }
        )
        return HttpResponseRedirect(form_url.url)

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
