from collections.abc import Iterator

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext, gettext_lazy as _

import structlog
from onlinepayments.sdk.api_exception import ApiException as WorldlineApiException
from onlinepayments.sdk.communication.request_header import RequestHeader
from onlinepayments.sdk.communicator import CommunicationException
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.webhooks.api_version_mismatch_exception import (
    ApiVersionMismatchException,
)
from onlinepayments.sdk.webhooks.signature_validation_exception import (
    SignatureValidationException,
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
from openforms.template import render_from_string, sandbox_backend
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.variables.utils import get_variables_for_context

from ...registry import register
from .constants import (
    HostedCheckoutStatus as WorldlineHostedCheckoutStatus,
    PaymentStatus as WorldlinePaymentStatus,
    StatusCategory,
)
from .models import WorldlineMerchant, WorldlineWebhookConfiguration
from .typing import (
    CheckoutInput,
    Order,
    PaymentOptions,
)
from .utils import get_webhook_helper

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
    variant = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        label=_("Variant name"),
        help_text=_(
            "Name of the template that should be used during the payment process. "
            'This can be found under the "Variant name" field in the "Branding" section.'
        ),
    )
    descriptor_template = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        label=_("Descriptor template"),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.sandbox_backend")
        ],
        help_text=_(
            "Optional custom template for the description, included in the payment "
            "overviews for the backoffice. Use this to link the payment back to a "
            "particular process or form. You can include all form variables (using "
            "their keys) and the 'public_reference' variable (using expression "
            "'{{ public_reference }}'). If unspecified, a default description is used. "
            "Note that the length of the result is capped to 32 characters."
        ),
    )
    _checkoutDetails = CheckoutSerializer(required=False)


def _generate_order(payment: SubmissionPayment, options: PaymentOptions) -> Order:
    public_reference = payment.submission.public_registration_reference
    default_description = f"{_('Submission')}: {public_reference}"
    template_context = get_variables_for_context(payment.submission)
    template_context["public_reference"] = public_reference
    descriptor = (
        render_from_string(
            descriptor_template, template_context, backend=sandbox_backend
        )
        if (descriptor_template := options.get("descriptor_template"))
        else default_description
    )

    return {
        "amountOfMoney": {
            "currencyCode": "EUR",
            "amount": int((payment.amount * 100).to_integral_exact()),
        },
        "references": {
            "merchantReference": payment.public_order_id,
            "descriptor": descriptor[:32],
        },
    }


def _generate_checkout_input(
    request: HttpRequest,
    payment: SubmissionPayment,
    options: PaymentOptions,
    payment_plugin: "WorldlinePaymentPlugin",
) -> CheckoutInput:
    return_url = payment_plugin.get_return_url(request, payment)

    if variant := options.get("variant"):
        return {"returnUrl": return_url, "variant": variant}

    return {"returnUrl": return_url}


@register("worldline")
class WorldlinePaymentPlugin(BasePlugin[PaymentOptions]):
    verbose_name = _("Wordline")
    configuration_options = WorldlineOptionsSerializer

    webhook_method = "POST"
    webhook_verification_method = "GET"
    webhook_verification_header = "X-GCS-Webhooks-Endpoint-Verification"

    def start_payment(
        self,
        request: HttpRequest,
        payment: SubmissionPayment,
        options: PaymentOptions,
    ) -> PaymentInfo:
        order = _generate_order(payment, options)
        checkout_input = _generate_checkout_input(request, payment, options, self)
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
                "variant": options["variant"],
                "descriptor_template": options["descriptor_template"],
                "_checkoutDetails": {
                    "RETURNMAC": checkout_response.returnmac,
                    "hostedCheckoutId": checkout_response.hosted_checkout_id,
                },
            }
        )

        valid_options = option_serializer.is_valid(raise_exception=False)

        assert valid_options, "Incorrect payment options encountered"

        payment.plugin_options = option_serializer.data
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
        merchant_reference: str,
    ) -> None:
        if payment.status in PAYMENT_STATUS_FINAL:
            # shouldn't happen or race-condition
            logger.warning(
                "payment_status_final",
                payment=payment,
                worldline_status=worldline_status,
                public_order_id=merchant_reference,
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
        result_count = queryset.update(
            status=status, public_order_id=merchant_reference
        )

        if result_count > 0:
            payment.refresh_from_db()

    def handle_return(
        self,
        request: Request,
        payment: SubmissionPayment,
        options: PaymentOptions,
    ) -> HttpResponse:
        if payment.status == PaymentStatus.completed:
            token = submission_status_token_generator.make_token(payment.submission)
            status_url = request.build_absolute_uri(
                reverse(
                    "api:submission-status",
                    kwargs={"uuid": payment.submission.uuid, "token": token},
                )
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

        with structlog.contextvars.bound_contextvars(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
            public_order_id=payment.public_order_id,
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

            if payment_data and payment_data.payment:
                status = WorldlinePaymentStatus(
                    payment_data.payment.status
                    if payment_data and payment_data.payment
                    else None
                )

                payment.provider_payment_id = payment_data.payment.id
                payment.save(update_fields=("provider_payment_id",))
            else:
                status = WorldlineHostedCheckoutStatus.to_payment_status(
                    checkout_status
                )

            self.apply_status(payment, status, payment.public_order_id)

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

    def handle_webhook(self, request: Request) -> SubmissionPayment | None:
        webhook_helper = get_webhook_helper()

        try:
            webhook_event = webhook_helper.unmarshal(
                request.body,
                request_headers=[
                    RequestHeader(header, request.headers[header])
                    for header in request.headers
                ],
            )
        except (SignatureValidationException, ApiVersionMismatchException) as e:
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [str(e)]}) from e

        if (
            not webhook_event.type
            or not webhook_event.type.startswith("payment")
            or not webhook_event.payment
        ):
            raise ValidationError(
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        _("Unknown webhook event encountered")
                    ]
                }
            )

        payment_response = webhook_event.payment

        assert payment_response.payment_output, "No payment output found in response"
        assert payment_response.payment_output.references, (
            "No payment references found in response"
        )
        merchant_reference = (
            payment_response.payment_output.references.merchant_reference
        )
        assert merchant_reference, "Merchant reference not found"

        try:
            payment = get_object_or_404(
                SubmissionPayment,
                public_order_id=merchant_reference,
            )
        except Http404:
            logger.warning(
                "unknown_payment",
                public_order_id=merchant_reference,
                plugin="worldline",
            )
            raise

        if payment.status == PaymentStatus.completed:
            return payment

        with structlog.contextvars.bound_contextvars(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
            public_order_id=merchant_reference,
            plugin=self,
            entrypoint="webhook",
        ):
            logger.info("process_payment_status")

            status = WorldlinePaymentStatus(webhook_event.payment.status)

            self.apply_status(
                payment,
                status,
                merchant_reference,
            )

            # Save the payment ID whenever this was not set yet whenever the user
            # got redirected. This can happen whenever no payment was created yet
            # after the user got redirected.
            if not payment.provider_payment_id:
                payment.provider_payment_id = webhook_event.payment.id
                payment.save(update_fields=("provider_payment_id",))

            return payment

    @classmethod
    def iter_config_checks(cls) -> Iterator[Entry]:
        merchants = WorldlineMerchant.objects.all()
        webhook_configurations = WorldlineWebhookConfiguration.objects.all()

        if not merchants:
            yield Entry(
                name=gettext("Worldline merchant"),
                actions=[
                    (
                        _("Add merchant"),
                        reverse(
                            "admin:payments_worldline_worldlinemerchant_add",
                        ),
                    )
                ],
                status=False,
            )

        for merchant in merchants:
            yield cls.check_merchant(merchant)

        if not webhook_configurations:
            yield Entry(
                name=gettext("Add worldline webhook configuration"),
                actions=[
                    (
                        _("Add webhook"),
                        reverse(
                            "admin:payments_worldline_worldlinewebhookconfiguration_add",
                        ),
                    )
                ],
                status=False,
            )

        for webhook_configuration in webhook_configurations:
            yield Entry(
                name=gettext("Worldline webhook configuration ({pspid})").format(
                    pspid=webhook_configuration.pspid or _("(no pspid)")
                ),
                actions=[
                    (
                        _("Configure webhook"),
                        reverse(
                            "admin:payments_worldline_worldlinewebhookconfiguration_change",
                            args=(webhook_configuration.pk,),
                        ),
                    )
                ],
                status=all(
                    (
                        webhook_configuration.webhook_key_id,
                        webhook_configuration.webhook_key_secret,
                    )
                ),
            )

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
