from typing import Any, Generator
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog
from onlinepayments.sdk.api_exception import ApiException
from onlinepayments.sdk.communicator import CommunicationException
from onlinepayments.sdk.communicator_configuration import CommunicatorConfiguration
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.merchant_client import IHostedCheckoutClient
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.request import Request

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.config.data import Entry
from openforms.frontend.frontend import get_frontend_redirect_url
from openforms.payments.base import BasePlugin, PaymentInfo
from openforms.payments.constants import (
    PAYMENT_STATUS_FINAL,
    PaymentRequestType,
    PaymentStatus,
)
from openforms.payments.contrib.worldline.constants import (
    get_payment_status,
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


class WorldlineOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant = PrimaryKeyRelatedAsChoicesField(
        queryset=WorldlineMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )


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
        client = options["merchant"].get_checkout_client()

        # See the hostedCheckoutSpecificInput field on
        # https://docs.direct.worldline-solutions.com/en/api-reference#tag/HostedCheckout/operation/CreateHostedCheckoutApi
        # for more configurable checkout options.
        checkout_request = CreateHostedCheckoutRequest()
        checkout_request.from_dictionary(
            {
                "returnCancelState": True,
                "hostedCheckoutSpecificInput": checkout_input,
                "order": order,
            }
        )

        try:
            checkout_response = client.create_hosted_checkout(checkout_request)
        except (ApiException, CommunicationException) as e:
            payment.status = PaymentStatus.failed
            payment.save(update_fields=("status",))

            raise APIException(
                detail="Failed to retrieve redirect URL from payment provider"
            ) from e

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
        self,
        payment: SubmissionPayment,
        worldline_status: str,
        checkout_status: str,
        payment_id: str,
    ) -> None:
        if payment.status in PAYMENT_STATUS_FINAL:
            # shouldn't happen or race-condition
            return

        status = get_payment_status(worldline_status, checkout_status=checkout_status)

        # run this query as atomic update()
        qs = SubmissionPayment.objects.filter(id=payment.id)
        qs = qs.exclude(status__in=PAYMENT_STATUS_FINAL)
        qs = qs.exclude(status=status)
        res = qs.update(status=status, provider_payment_id=payment_id)

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

            client = options["merchant"].get_checkout_client()

            try:
                response = client.get_hosted_checkout(checkout_id)
            except ApiException:
                return HttpResponseServerError(b"Unable to retrieve checkout status")

            payment_data = response.created_payment_output
            checkout_status = response.status
            status = (
                payment_data.payment.status
                if payment_data and payment_data.payment
                else ""
            )

            payment_provider_id = (
                payment_data.payment.id if payment_data and payment_data.payment else ""
            )

            self.apply_status(
                payment,
                status,
                checkout_status,
                payment_provider_id,
            )

            redirect_url = get_frontend_redirect_url(
                payment.submission,
                action="payment",
                action_params={
                    "of_payment_status": payment.status,
                    "of_payment_id": str(payment.uuid),
                    "of_submission_status": status_url,
                },
            )
            return HttpResponseRedirect(redirect_url)

    # TODO
    def handle_webhook(self, request: Request) -> SubmissionPayment:
        raise NotImplementedError()

    @classmethod
    def iter_config_checks(cls) -> Generator[Entry, Any, Any]:
        for merchant in WorldlineMerchant.objects.all():
            yield cls.check_merchant(merchant)

    @classmethod
    def check_merchant(cls, merchant: WorldlineMerchant):
        entry = Entry(
            name=f"{cls.verbose_name}: {merchant.label}",
            actions=[
                (
                    _("Configuration"),
                    reverse(
                        "admin:payments_worldline_worldlinemerchant_change",
                        args=(merchant.pk,),
                    ),
                )
            ],
        )

        merchant_client = merchant.get_merchant_client()

        try:
            merchant_client.services().test_connection()
        except Exception as e:
            entry.status = False
            entry.error = str(e)
            print(e)
        else:
            entry.status = True
        return entry
