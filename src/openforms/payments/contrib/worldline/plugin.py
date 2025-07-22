from configparser import ConfigParser
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from onlinepayments.sdk.client import Client
from onlinepayments.sdk.communicator_configuration import CommunicatorConfiguration
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.merchant_client import HostedCheckoutClient
from rest_framework import serializers
from rest_framework.request import Request

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.payments.base import BasePlugin, PaymentInfo
from openforms.payments.constants import PaymentRequestType
from openforms.payments.contrib.ogone.typing import PaymentOptions
from openforms.payments.contrib.worldline.models import WorldlineMerchant
from openforms.payments.models import SubmissionPayment
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...registry import register


# TODO: add configurable template fields?
class WorldlineOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant_id = PrimaryKeyRelatedAsChoicesField(
        queryset=WorldlineMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )


# TODO:
def _construct_config_from_options(options: PaymentOptions) -> ConfigParser
    pass


# TODO: add logging events
@register("worldline")
class WorldlinePaymentPlugin(BasePlugin[PaymentOptions]):
    verbose_name = _("Wordline")
    configuration_options = WorldlineOptionsSerializer

    def start_payment(
        self,
        request: HttpRequest,
        payment: SubmissionPayment,
        options: PaymentOptions, # TODO: replace these options with worldline payment options
    ) -> PaymentInfo:
        amount_cents = int((payment.amount * 100).to_integral_exact())

        config_parser = _construct_config_from_options(options)
        communicator_configuration = CommunicatorConfiguration(config_parser)

        # TODO: should we construct this manually from a ConfigParser object?
        client = Factory.create_client_from_configuration(
            communicator_configuration
        )

        merchant_client = client.merchant(options["merchant_id"])
        checkout_client = merchant_client.hosted_checkout()

        try:
            response = checkout_client.create_hosted_checkout(
                CreateHostedCheckoutRequest()
            )
        except:  # TODO: implement proper error handling
            raise ValueError

        response_data: dict = response.to_dictionary()
        return PaymentInfo(
            type=PaymentRequestType.get, url=response_data["redirect_url"] # TODO: should the redirect_url be returned here?
        )

    def handle_return(
        self,
        request: Request,
        payment: SubmissionPayment,
        options: PaymentOptions,
    ) -> HttpResponse:
        raise NotImplementedError()

    def handle_webhook(self, request: Request) -> SubmissionPayment:
        raise NotImplementedError()
