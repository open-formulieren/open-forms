import logging

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from openforms.logging import logevent
from openforms.utils.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...base import BasePlugin
from ...constants import PaymentStatus, UserAction
from ...contrib.ogone.client import OgoneClient
from ...contrib.ogone.constants import OgoneStatus
from ...contrib.ogone.exceptions import InvalidSignature
from ...contrib.ogone.models import OgoneMerchant
from ...models import SubmissionPayment
from ...registry import register

logger = logging.getLogger(__name__)


class OgoneOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant_id = PrimaryKeyRelatedAsChoicesField(
        queryset=OgoneMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )


RETURN_ACTION_PARAM = "action"


@register("ogone-legacy")
class OgoneLegacyPaymentPlugin(BasePlugin):
    verbose_name = _("Ogone legacy")
    configuration_options = OgoneOptionsSerializer

    def start_payment(self, request, payment: SubmissionPayment):
        # decimal to cents
        amount_cents = int((payment.amount * 100).to_integral_exact())

        merchant = get_object_or_404(
            OgoneMerchant, id=payment.plugin_options["merchant_id"]
        )
        client = OgoneClient(merchant)

        return_url = self.get_return_url(request, payment)

        description = (
            f"{_('Submission')}: {payment.submission.public_registration_reference}"
        )

        info = client.get_payment_info(
            payment.public_order_id,
            amount_cents,
            return_url,
            RETURN_ACTION_PARAM,
            description,
        )
        return info

    def handle_return(self, request, payment: SubmissionPayment):
        action = request.query_params.get(RETURN_ACTION_PARAM)

        merchant = get_object_or_404(
            OgoneMerchant, id=payment.plugin_options["merchant_id"]
        )
        client = OgoneClient(merchant)

        try:
            params = client.get_validated_params(request.query_params)
        except InvalidSignature as e:
            logger.warning(f"invalid SHASIGN for payment {payment}")
            logevent.payment_flow_failure(payment, self, e)
            return HttpResponseBadRequest("bad shasign")

        self.apply_status(payment, params.STATUS)

        form_url = furl(payment.submission.form_url)
        form_url.args.update(
            {
                "of_payment_status": payment.status,
                "of_payment_id": str(payment.uuid),
                "of_payment_action": action or UserAction.unknown,
            }
        )
        return HttpResponseRedirect(form_url.url)

    def handle_webhook(self, request):
        # unvalidated data
        order_id = case_insensitive_get(request.data, "orderID")
        if not order_id:
            # we use ParseError in this method because serializers.ValidationError triggers exception serializers
            raise ParseError("missing orderID")

        payment = get_object_or_404(SubmissionPayment, public_order_id=order_id)
        merchant = get_object_or_404(
            OgoneMerchant, id=payment.plugin_options["merchant_id"]
        )
        client = OgoneClient(merchant)

        try:
            params = client.get_validated_params(request.data)
        except InvalidSignature as e:
            logger.warning(f"invalid SHASIGN for payment {payment}")
            logevent.payment_flow_failure(payment, self, e)
            # see note about ParseError above
            raise ParseError("bad shasign")

        self.apply_status(payment, params.STATUS)

        return payment

    def apply_status(self, payment, ogone_status) -> None:
        if payment.status in PaymentStatus.is_final:
            # shouldn't happen or race-condition
            return

        new_status = OgoneStatus.as_payment_status(ogone_status)

        # run this query as atomic update()
        qs = SubmissionPayment.objects.filter(id=payment.id).select_for_update()
        qs = qs.exclude(status__in=PaymentStatus.is_final)
        qs = qs.exclude(status=new_status)
        res = qs.update(status=new_status)

        if res > 0:
            payment.refresh_from_db()


def case_insensitive_get(mapping, key, default=None):
    if key in mapping:
        return mapping[key]
    for k in mapping:
        if k.upper() == key.upper():
            return mapping[k]
    return default
