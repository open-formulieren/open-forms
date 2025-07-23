from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

import structlog
from onlinepayments.sdk.api_exception import ApiException
from onlinepayments.sdk.communicator_configuration import CommunicatorConfiguration
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.merchant_client import IHostedCheckoutClient
from rest_framework import serializers
from rest_framework.request import Request

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.frontend.frontend import get_frontend_redirect_url
from openforms.payments.base import BasePlugin, PaymentInfo
from openforms.payments.constants import PaymentRequestType
from openforms.payments.contrib.worldline.models import WorldlineMerchant
from openforms.payments.contrib.worldline.typing import (
    AmountOfMoney,
    CheckoutInput,
    Order,
    PaymentOptions,
)
from openforms.payments.models import SubmissionPayment
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...registry import register

logger = structlog.stdlib.get_logger(__name__)


# TODO: add configurable template fields?
class WorldlineOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant = PrimaryKeyRelatedAsChoicesField(
        queryset=WorldlineMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )


def _construct_client_from_options(options: PaymentOptions) -> IHostedCheckoutClient:
    merchant = options["merchant"]

    configuration = CommunicatorConfiguration(
        api_endpoint=merchant.endpoint,
        api_key_id=merchant.api_key,
        secret_api_key=merchant.api_secret,
        authorization_type="v1HMAC",
        integrator="openforms-test-sonny",  #  TODO: retrieve this from?
        connect_timeout=5000,
        socket_timeout=10000,
        max_connections=10,
    )

    communicator = Factory.create_communicator_from_configuration(configuration)
    client = Factory.create_client_from_communicator(communicator)
    merchant_client = client.merchant(merchant.pspid)
    return merchant_client.hosted_checkout()


def _generate_order(payment: SubmissionPayment) -> Order:
    amount_of_money = AmountOfMoney(
        currencyCode="EUR", amount=int((payment.amount * 100).to_integral_exact())
    )
    return Order(amountOfMoney=amount_of_money)


def _generate_checkout_input(
    request: HttpRequest,
    payment: SubmissionPayment,
    payment_plugin: "WorldlinePaymentPlugin",
) -> CheckoutInput:
    return_url = payment_plugin.get_return_url(request, payment)
    return CheckoutInput(returnUrl=return_url)


@register("worldline")
class WorldlinePaymentPlugin(BasePlugin[PaymentOptions]):
    verbose_name = _("Wordline")
    configuration_options = WorldlineOptionsSerializer

    def start_payment(
        self,
        request: HttpRequest,
        payment: SubmissionPayment,
        options: PaymentOptions,
    ) -> PaymentInfo:
        order = _generate_order(payment)
        checkout_input = _generate_checkout_input(request, payment, self)
        client = _construct_client_from_options(options)

        # See the hostedCheckoutSpecificInput field on
        # https://docs.direct.worldline-solutions.com/en/api-reference#tag/HostedCheckout/operation/CreateHostedCheckoutApi
        # for more configurable checkout options.
        checkout_request = CreateHostedCheckoutRequest()
        checkout_request.from_dictionary(
            {"hostedCheckoutSpecificInput": checkout_input, "order": order}
        )

        try:
            checkout_response = client.create_hosted_checkout(checkout_request)
        except ApiException as e:
            raise Exception(
                "Failed to generate redirect URL to payment provider"
            ) from e  # TODO: handle this situation in a more user friendly way

        # TODO: save RETURNMAC and hosted_checkout_id on SubmissionPayment?

        return PaymentInfo(
            type=PaymentRequestType.get,
            url=checkout_response.redirect_url,  # valid for three hours
            data={},
        )

    # TODO
    def handle_return(
        self,
        request: Request,
        payment: SubmissionPayment,
        options: PaymentOptions,
    ) -> HttpResponse:
        with structlog.contextvars.bound_contextvars(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
            plugin=self,
            entrypoint="browser",
        ):
            action = request.query_params.get(RETURN_ACTION_PARAM)
            payment_id = request.query_params[PAYMENT_ID_PARAM]
            log = logger.bind(payment_id=payment_id)

            log.info("process_payment_status")

            # TODO: verify RETURNMAC and hosted_checkout_id match with the saved values
            # retrieved from the start of the payment process, see https://docs.connect.worldline-solutions.com/documentation/sdk/server/python/#use-a-hosted-payment-through-the-mycheckout-hosted-payment-pages

            redirect_url = get_frontend_redirect_url(
                payment.submission,
                action="payment",
                action_params={
                    "of_payment_status": payment.status,
                    "of_payment_id": str(payment.uuid),
                    "of_payment_action": action or UserAction.unknown,
                    "of_submission_status": status_url,
                },
            )
            return HttpResponseRedirect(redirect_url)

    # TODO
    def handle_webhook(self, request: Request) -> SubmissionPayment:
        raise NotImplementedError()
