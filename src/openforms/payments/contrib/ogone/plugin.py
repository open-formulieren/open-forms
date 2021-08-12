from dataclasses import asdict

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework import serializers, status
from rest_framework.response import Response

from openforms.payments.base import BasePlugin
from openforms.payments.constants import PaymentStatus, UserAction
from openforms.payments.contrib.ogone.client import OgoneClient
from openforms.payments.contrib.ogone.constants import OgoneStatus
from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.models import SubmissionPayment
from openforms.payments.registry import register


class OgoneOptionsSerializer(serializers.Serializer):
    merchant_id = serializers.PrimaryKeyRelatedField(
        queryset=OgoneMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )


@register("ogone-legacy")
class OgoneLegacyPaymentPlugin(BasePlugin):
    verbose_name = _("Ogone Legacy")
    configuration_options = OgoneOptionsSerializer

    def start_payment(self, request, payment: SubmissionPayment):
        # decimal to cents
        amount_cents = round(payment.amount * 100)

        merchant = get_object_or_404(OgoneMerchant, id=payment.options["merchant_id"])
        client = OgoneClient(merchant)

        return_url = self.get_return_url(request, payment)

        info = client.get_payment_info(
            payment.order_id, amount_cents, return_url, "action"
        )
        return info

    def handle_return(self, request, payment: SubmissionPayment):
        action = request.GET.get("action")

        merchant = get_object_or_404(OgoneMerchant, id=payment.options["merchant_id"])
        client = OgoneClient(merchant)

        try:
            params = client.get_validated_params(request.query_params)
        except ValueError:
            # TODO log this
            return HttpResponseBadRequest("bad shasign")

        self.apply_status(payment, params.STATUS)

        form_url = furl(payment.form_url)
        form_url.args["of_payment_status"] = payment.status
        form_url.args["of_payment_id"] = str(payment.uuid)
        form_url.args["of_payment_action"] = action or UserAction.unknown
        return HttpResponseRedirect(form_url.url)

    def handle_webhook(self, request):
        # unvalidated data
        order_id = request.data.get("ORDERID")
        if not order_id:
            return HttpResponseBadRequest("missing ORDERID")
        payment = get_object_or_404(SubmissionPayment, remote_order_id=order_id)
        merchant = get_object_or_404(OgoneMerchant, id=payment.options["merchant_id"])
        client = OgoneClient(merchant)

        try:
            params = client.get_validated_params(request.DATA)
        except ValueError:
            return HttpResponseBadRequest("bad shasign")

        self.apply_status(payment, params.STATUS)

    def apply_status(self, payment, ogone_status) -> None:
        if payment.status in PaymentStatus.is_final:
            # shouldn't happen or race-condition
            return

        new_status = OgoneStatus.as_payment_status(ogone_status)
        if payment.status != new_status:
            payment.status = new_status
            payment.save()
