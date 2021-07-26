from dataclasses import asdict

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework import serializers, status
from rest_framework.response import Response

from openforms.payments.base import BasePlugin
from openforms.payments.constants import UserAction
from openforms.payments.contrib.ogone.client import OgoneClient
from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.registry import register


class OgoneOptionsSerializer(serializers.Serializer):
    # merchant_id = serializers.PrimaryKeyRelatedField(
    #     queryset=OgoneMerchantConfig.objects.all(),
    #     required=True,
    #     help_text=_("Merchant to use"),
    # )
    pass


@register("ogone-legacy")
class OgoneLegacyPaymentPlugin(BasePlugin):
    verbose_name = _("Ogone Legacy")
    configuration_options = OgoneOptionsSerializer

    def start_payment(
        self, request, form, form_url, options, submission, payment_amount_cents
    ):
        merchant = get_object_or_404(OgoneMerchant, id=options["merchant_id"])
        client = OgoneClient(merchant)

        registration_id = submission.get_registration_id()

        return_url = furl(self.get_return_url(request, form))
        return_url.args["next"] = form_url

        info = client.get_payment_info(
            registration_id, payment_amount_cents, return_url.url, "action"
        )
        # TODO add generic dataclass serializer
        return Response(asdict(info), status=status.HTTP_200_OK)

    def handle_return(self, request, form):
        form_url = request.GET.get("next")
        action = request.GET.get("action")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        # TODO see if we have server-2-server result

        form_url = furl(form_url)
        form_url.args["of_payment_action"] = action or UserAction.unknown
        return HttpResponseRedirect(form_url.url)
