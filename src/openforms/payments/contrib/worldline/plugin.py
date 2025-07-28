from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.urls import reverse
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
from openforms.payments.constants import (
    PAYMENT_STATUS_FINAL,
    PaymentRequestType,
    UserAction,
)
from openforms.payments.contrib.worldline.constants import (
    StatusCategory,
    get_user_action,
)
from openforms.payments.contrib.worldline.models import WorldlineMerchant
from openforms.payments.contrib.worldline.typing import (
    AmountOfMoney,
    CheckoutInput,
    Order,
    PaymentOptions,
)
from openforms.payments.models import SubmissionPayment
from openforms.submissions.tokens import submission_status_token_generator
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
        integrator="openforms",  #  TODO: is this the correct value?
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

        plugin_options = payment.plugin_options
        payment.plugin_options = {
            **plugin_options,
            "returnmac": checkout_response.returnmac,
            "checkout_id": checkout_response.hosted_checkout_id,
        }

        payment.save(update_fields=("plugin_options",))

        return PaymentInfo(
            type=PaymentRequestType.get,
            url=checkout_response.redirect_url,  # valid for three hours
            data={},
        )

    def apply_status(
        self, payment: SubmissionPayment, worldline_status: str, payment_id: str
    ) -> None:
        if payment.status in PAYMENT_STATUS_FINAL:
            # shouldn't happen or race-condition
            return

        status_category = StatusCategory.from_payment_status(worldline_status)
        new_status = StatusCategory.to_of_status(status_category)

        # run this query as atomic update()
        qs = SubmissionPayment.objects.filter(id=payment.id)
        qs = qs.exclude(status__in=PAYMENT_STATUS_FINAL)
        qs = qs.exclude(status=new_status)
        res = qs.update(status=new_status, provider_payment_id=payment_id)

        if res > 0:
            payment.refresh_from_db()

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
            log = logger.bind()
            log.info("process_payment_status")

            returnmac = payment.plugin_options.get("returnmac", "")
            checkout_id = payment.plugin_options.get("checkout_id", "")

            if (
                not request.query_params.get("RETURNMAC") == returnmac
                or not request.query_params.get("hostedCheckoutId") == checkout_id
            ):
                return HttpResponseBadRequest(b"Incorrect query parameters provided")

            token = submission_status_token_generator.make_token(payment.submission)
            status_url = request.build_absolute_uri(
                reverse(
                    "api:submission-status",
                    kwargs={"uuid": payment.submission.uuid, "token": token},
                )
            )

            client = _construct_client_from_options(options)

            try:
                response = client.get_hosted_checkout(checkout_id)
            except ApiException:
                return HttpResponseBadRequest(
                    b"Unable to retrieve checkout status"
                )  # TODO: return in a more user friendly way

            payment_data = response.created_payment_output
            status = (
                payment_data.payment.status
                if payment_data and payment_data.payment
                else None
            )

            if not payment_data:
                return HttpResponseBadRequest(
                    b"No payment associated with the given checkout."
                )  # TODO: return in a more user friendly way
            elif not status:
                return HttpResponseBadRequest(
                    b"No status associated with the given payment."
                )

            self.apply_status(payment, status, payment.provider_payment_id)

            redirect_url = get_frontend_redirect_url(
                payment.submission,
                action="payment",
                action_params={
                    "of_payment_status": payment.status,
                    "of_payment_id": str(payment.uuid),
                    "of_payment_action": get_user_action(status),
                    "of_submission_status": status_url,
                },
            )
            return HttpResponseRedirect(redirect_url)

    # TODO
    def handle_webhook(self, request: Request) -> SubmissionPayment:
        raise NotImplementedError()
