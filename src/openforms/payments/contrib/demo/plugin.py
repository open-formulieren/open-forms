from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from openforms.payments.base import BasePlugin, PaymentInfo
from openforms.payments.constants import PaymentStatus
from openforms.payments.registry import register


@register("demo")
class DemoPayment(BasePlugin):
    verbose_name = _("Demo")
    is_demo_plugin = True

    def start_payment(self, request, payment):
        url = self.get_return_url(request, payment)
        return PaymentInfo(url=url)

    def handle_return(self, request, payment):
        payment.status = PaymentStatus.completed
        payment.save()
        return HttpResponseRedirect(payment.form_url)
