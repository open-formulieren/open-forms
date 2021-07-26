from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from openforms.payments.base import BasePlugin
from openforms.payments.registry import register


@register("demo")
class DemoPayment(BasePlugin):
    verbose_name = _("Demo")

    def start_payment(
        self, request, form, form_url, registration_id, payment_amount_cents
    ):
        url = self.get_return_url(request, form)
        params = {
            # "return": self.get_return_url(request, form),
            "next": form_url,
            # "cancel": form_url,
        }
        url = f"{url}?{urlencode(params)}"
        return HttpResponseRedirect(url)

    def handle_return(self, request, form):
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        return HttpResponseRedirect(form_url)
