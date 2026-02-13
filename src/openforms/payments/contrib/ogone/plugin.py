from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from rest_framework.request import Request

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.config.data import Entry
from openforms.frontend import get_frontend_redirect_url
from openforms.logging import audit_logger
from openforms.submissions.tokens import submission_status_token_generator
from openforms.template import render_from_string, sandbox_backend
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.variables.service import get_variables_for_context

from ...base import BasePlugin
from ...constants import PAYMENT_STATUS_FINAL, UserAction
from ...models import SubmissionPayment
from ...registry import register
from .client import OgoneClient
from .constants import OgoneStatus
from .exceptions import InvalidSignature
from .models import OgoneMerchant
from .typing import PaymentOptions

logger = structlog.stdlib.get_logger(__name__)


class OgoneOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    merchant_id = PrimaryKeyRelatedAsChoicesField(
        queryset=OgoneMerchant.objects.all(),
        required=True,
        help_text=_("Merchant to use"),
    )
    title_template = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        label=_("TITLE template"),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.sandbox_backend")
        ],
        help_text=_(
            "Optional custom template for the title displayed on the payment page. "
            "You can include all form variables (using their keys) and the "
            "'public_reference' variable (using expression '{{ public_reference }}'). "
            "If unspecified, a default description is used."
        ),
    )
    com_template = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        label=_("COM template"),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.sandbox_backend")
        ],
        help_text=_(
            "Optional custom template for the description, included in the payment "
            "overviews for the backoffice. Use this to link the payment back to a "
            "particular process or form. You can include all form variables (using "
            "their keys) and the 'public_reference' variable (using expression "
            "'{{ public_reference }}'). If unspecified, a default description is used. "
            "Note that the length of the result is capped to 100 characters and only "
            "alpha-numeric characters are allowed."
        ),
    )


RETURN_ACTION_PARAM = "action"
PAYMENT_ID_PARAM = "PAYID"


@register("ogone-legacy")
class OgoneLegacyPaymentPlugin(BasePlugin[PaymentOptions]):
    verbose_name = _("Ogone legacy")
    configuration_options = OgoneOptionsSerializer

    def start_payment(
        self, request: HttpRequest, payment: SubmissionPayment, options: PaymentOptions
    ):
        # decimal to cents
        amount_cents = int((payment.amount * 100).to_integral_exact())

        client = OgoneClient(options["merchant_id"])

        return_url = self.get_return_url(request, payment)

        public_reference = payment.submission.public_registration_reference
        default_description = f"{_('Submission')}: {public_reference}"

        # evaluate custom templates, if specified
        template_context = get_variables_for_context(payment.submission)
        template_context["public_reference"] = public_reference

        title_value = (
            render_from_string(
                title_template, template_context, backend=sandbox_backend
            )
            if (title_template := options["title_template"])
            else default_description
        )
        com_value = (
            render_from_string(com_template, template_context, backend=sandbox_backend)
            if (com_template := options["com_template"])
            else default_description
        )

        info = client.get_payment_info(
            payment.public_order_id,
            amount_cents,
            return_url,
            RETURN_ACTION_PARAM,
            title=title_value,
            com=com_value[:100],
        )
        return info

    def handle_return(
        self, request: Request, payment: SubmissionPayment, options: PaymentOptions
    ):
        with structlog.contextvars.bound_contextvars(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
            plugin=self,
            entrypoint="browser",
        ):
            action = request.query_params.get(RETURN_ACTION_PARAM)
            payment_id = request.query_params[PAYMENT_ID_PARAM]
            log = logger.bind(payment_id=payment_id)
            audit_log = audit_logger.bind(**structlog.get_context(log))

            log.info("process_payment_status")
            client = OgoneClient(options["merchant_id"])

            try:
                params = client.get_validated_params(request.query_params)
            except InvalidSignature as exc:
                audit_log.warning(
                    "payment_flow_failure",
                    reason="invalid_shasign_signature",
                    exc_info=exc,
                )
                return HttpResponseBadRequest("bad shasign")

            self.apply_status(payment, params.STATUS, payment_id)

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
                    "of_payment_action": action or UserAction.unknown,
                    "of_submission_status": status_url,
                },
            )
            return HttpResponseRedirect(redirect_url)

    def handle_webhook(self, request: Request):
        # unvalidated data
        order_id = case_insensitive_get(request.data, "orderID")
        if not order_id:
            # we use ParseError in this method because serializers.ValidationError triggers exception serializers
            raise ParseError("missing orderID")

        payment_id = case_insensitive_get(request.data, "PAYID")
        if not payment_id:
            # we use ParseError in this method because serializers.ValidationError triggers exception serializers
            raise ParseError("missing PAYID")

        payment = get_object_or_404(SubmissionPayment, public_order_id=order_id)
        with structlog.contextvars.bound_contextvars(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
            plugin=self,
            entrypoint="webhook",
        ):
            log = logger.bind(payment_id=payment_id)
            audit_log = audit_logger.bind(**structlog.get_context(log))
            log.info("process_payment_status")

            options_serializer = self.configuration_options(data=payment.plugin_options)
            options_serializer.is_valid(raise_exception=True)
            options: PaymentOptions = options_serializer.validated_data
            client = OgoneClient(options["merchant_id"])

            try:
                params = client.get_validated_params(request.data)
            except InvalidSignature as exc:
                audit_log.warning(
                    "payment_flow_failure",
                    reason="invalid_shasign_signature",
                    exc_info=exc,
                )
                # see note about ParseError above
                raise ParseError("bad shasign")

            self.apply_status(payment, params.STATUS, payment_id)

            return payment

    def apply_status(
        self, payment: SubmissionPayment, ogone_status: str, payment_id: str
    ) -> None:
        if payment.status in PAYMENT_STATUS_FINAL:
            # shouldn't happen or race-condition
            return

        new_status = OgoneStatus.as_payment_status(ogone_status)

        # run this query as atomic update()
        qs = SubmissionPayment.objects.filter(id=payment.id)
        qs = qs.exclude(status__in=PAYMENT_STATUS_FINAL)
        qs = qs.exclude(status=new_status)
        res = qs.update(status=new_status, provider_payment_id=payment_id)

        if res > 0:
            payment.refresh_from_db()

    @classmethod
    def iter_config_checks(cls):
        for merchant in OgoneMerchant.objects.all():
            yield cls.check_merchant(merchant)

    @classmethod
    def check_merchant(cls, merchant):
        entry = Entry(
            name=f"{cls.verbose_name}: {merchant.label}",
            actions=[
                (
                    _("Configuration"),
                    reverse(
                        "admin:payments_ogone_ogonemerchant_change",
                        args=(merchant.pk,),
                    ),
                )
            ],
        )
        try:
            response = requests.get(merchant.endpoint)
            response.raise_for_status()
        except Exception as e:
            entry.status = False
            entry.error = str(e)
        else:
            entry.status = True
        return entry


def case_insensitive_get(mapping, key, default=None):
    if key in mapping:
        return mapping[key]
    for k in mapping:
        if k.upper() == key.upper():
            return mapping[k]
    return default
