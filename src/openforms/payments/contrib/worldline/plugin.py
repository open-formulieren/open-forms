from collections.abc import Iterator

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _

import structlog
from onlinepayments.sdk.api_exception import ApiException as WorldlineApiException
from onlinepayments.sdk.communicator import CommunicationException
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.settings import api_settings

from openforms.api.fields import SlugRelatedAsChoicesField
from openforms.config.data import Entry
from openforms.frontend.frontend import get_frontend_redirect_url
from openforms.payments.base import BasePlugin, PaymentInfo
from openforms.payments.constants import (
    PAYMENT_STATUS_FINAL,
    PaymentRequestType,
    PaymentStatus,
)
from openforms.payments.models import SubmissionPayment
from openforms.submissions.tokens import submission_status_token_generator
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ...registry import register
from .constants import (
    HostedCheckoutStatus as WorldlineHostedCheckoutStatus,
    PaymentStatus as WorldlinePaymentStatus,
    StatusCategory,
)
from .models import WorldlineMerchant
from .typing import (
    AmountOfMoney,
    CheckoutInput,
    Order,
    PaymentOptions,
)

logger = structlog.stdlib.get_logger(__name__)


class CheckoutSerializer(serializers.Serializer):
    RETURNMAC = serializers.CharField()
    hostedCheckoutId = serializers.CharField()


class WorldlineOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant = SlugRelatedAsChoicesField(
        queryset=WorldlineMerchant.objects.all(),
        slug_field="pspid",
        required=True,
        help_text=_("Merchant to use"),
    )

    _checkoutDetails = CheckoutSerializer(required=False)


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
        except (WorldlineApiException, CommunicationException) as e:
            payment.status = PaymentStatus.failed
            payment.save(update_fields=("status",))

            raise APIException(
                detail="Failed to retrieve redirect URL from payment provider"
            ) from e

        assert checkout_response.redirect_url, (
            "Missing redirect url in Worldline response"
        )

        option_serializer = self.configuration_options(
            data={
                "merchant": options["merchant"].pspid,
                "_checkoutDetails": {
                    "RETURNMAC": checkout_response.returnmac,
                    "hostedCheckoutId": checkout_response.hosted_checkout_id,
                },
            }
        )

        valid_options = option_serializer.is_valid(raise_exception=False)

        assert valid_options, "Incorrect payment options encountered"

        payment.plugin_options = option_serializer.data
        payment.provider_payment_id = checkout_response.merchant_reference or ""
        payment.save(update_fields=("plugin_options",))

        return PaymentInfo(
            type=PaymentRequestType.get,
            url=checkout_response.redirect_url,  # valid for three hours
            data={},
        )

    def apply_status(
        self,
        payment: SubmissionPayment,
        worldline_status: WorldlinePaymentStatus,
        payment_id: str,
    ) -> None:
        if payment.status in PAYMENT_STATUS_FINAL:
            # shouldn't happen or race-condition
            logger.warning(
                "payment_status_final",
                payment=payment,
                worldline_status=worldline_status,
                payment_id=payment_id,
            )
            return

        status_category = StatusCategory.from_payment_status(worldline_status)
        status = StatusCategory.to_of_status(status_category)

        # run this query as atomic update()
        queryset = (
            SubmissionPayment.objects.filter(id=payment.id)
            .exclude(status__in=PAYMENT_STATUS_FINAL)
            .exclude(status=status)
        )
        result_count = queryset.update(status=status, provider_payment_id=payment_id)

        if result_count > 0:
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
            logger.info("process_payment_status")

            checkout_details = options["_checkoutDetails"] or {}
            returnmac = checkout_details.get("RETURNMAC", "")
            checkout_id = checkout_details.get("hostedCheckoutId", "")

            if not constant_time_compare(
                request.query_params.get("RETURNMAC"),  # pyright: ignore[reportArgumentType]
                returnmac,
            ) or not constant_time_compare(
                request.query_params.get("hostedCheckoutId"),  # pyright: ignore[reportArgumentType]
                checkout_id,
            ):
                raise ValidationError(
                    {
                        api_settings.NON_FIELD_ERRORS_KEY: [
                            "Incorrect query parameters provided"
                        ]
                    }
                )

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
            except WorldlineApiException as exc:
                raise APIException("Unable to retrieve checkout status") from exc

            checkout_status = WorldlineHostedCheckoutStatus(response.status)
            payment_data = response.created_payment_output
            try:
                status = WorldlinePaymentStatus(
                    payment_data.payment.status
                    if payment_data and payment_data.payment
                    else None
                )
            except ValueError:
                status = WorldlineHostedCheckoutStatus.to_payment_status(
                    checkout_status
                )

            external_payment_id = (
                payment_data.payment.payment_output.references.merchant_reference
                if payment_data
                and payment_data.payment
                and payment_data.payment.payment_output
                and payment_data.payment.payment_output.references
                else None
            )

            assert external_payment_id, (
                "No merchant reference found in checkout status response"
            )

            self.apply_status(payment, status, external_payment_id)

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
    def iter_config_checks(cls) -> Iterator[Entry]:
        merchants = WorldlineMerchant.objects.all()

        if not merchants:
            yield Entry(
                name="Worldline merchant",
                actions=[
                    (
                        _("Add merchant"),
                        reverse(
                            "admin:payments_worldline_worldlinemerchant_add",
                        ),
                    )
                ],
            )

        for merchant in merchants:
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
        else:
            entry.status = True
        return entry
