from functools import partial

from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView

import structlog
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import permissions, status
from rest_framework.exceptions import MethodNotAllowed, NotFound, ParseError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.parsers import PlainTextParser
from openforms.api.serializers import ExceptionSerializer
from openforms.api.views import ERR_CONTENT_TYPE
from openforms.logging import audit_logger
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.models import Submission
from openforms.submissions.tasks import on_post_submission_event
from openforms.utils.redirect import allow_redirect_url

from .api.serializers import PaymentInfoSerializer
from .constants import PaymentStatus
from .models import SubmissionPayment
from .registry import register

logger = structlog.stdlib.get_logger(__name__)


class PaymentFlowBaseView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)


@extend_schema(
    summary=_("Start payment flow"),
    description=_(
        "This endpoint provides information to start the payment flow for a submission."
        "\n\nDue to support for legacy platforms this view doesn't redirect but provides "
        "information for the frontend to be used client side."
        "\n\nVarious validations are performed:"
        "\n* the form and submission must require payment"
        "\n* the `plugin_id` is configured on the form"
        "\n* payment is required and configured on the form"
        "\n* the `next` parameter must be present"
        "\n* the `next` parameter must match the CORS policy"
        "\n\nThe HTTP 200 response contains the information to start the flow with the "
        "payment provider. Depending on the 'type', send a `GET` or `POST` request with "
        "the `data` as 'Form Data' to the given 'url'."
    ),
    parameters=[
        OpenApiParameter(
            name="uuid",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("UUID identifying the submission."),
        ),
        OpenApiParameter(
            name="plugin_id",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_(
                "Identifier of the payment plugin. Note that this is validated "
                "against the configured available plugins for this particular form."
            ),
        ),
        OpenApiParameter(
            name="next",
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.URI,
            description=_(
                "URL of the form to redirect back to. This URL is validated "
                "against the CORS configuration."
            ),
            required=True,
        ),
    ],
    request=None,
    responses={
        200: PaymentInfoSerializer,
        (400, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Bad request. Invalid parameters were passed."),
        ),
        (404, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_(
                "Not found. The slug did not point to a live submission or the "
                "`plugin_id` does not exist."
            ),
        ),
    },
)
class PaymentStartView(PaymentFlowBaseView, GenericAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    queryset = Submission.objects.exclude(completed_on__isnull=True)
    serializer_class = PaymentInfoSerializer

    def post(self, request, uuid: str, plugin_id: str):
        submission: Submission = self.get_object()
        assert submission.public_registration_reference

        try:
            plugin = register[plugin_id]
        except KeyError:
            raise NotFound(detail="unknown plugin")

        if not submission.payment_required:
            raise ParseError(detail="payment not required")

        if not plugin.is_enabled:
            raise ParseError(detail="plugin not enabled")

        if plugin_id != submission.form.payment_backend:
            raise ParseError(detail="plugin not allowed")

        payment = SubmissionPayment.objects.create_for(
            submission,
            plugin_id,
            submission.form.payment_backend_options,
            submission.price,
        )

        options = plugin.configuration_options(data=payment.plugin_options)
        options.is_valid(raise_exception=True)
        info = plugin.start_payment(request, payment, options.validated_data)
        audit_logger.info(
            "payment_flow_start",
            submission_uuid=str(payment.submission.uuid),
            plugin=plugin,
            payment_uuid=str(payment.uuid),
        )
        return Response(self.get_serializer(instance=info).data)


@extend_schema(
    summary=_("Return from external payment flow"),
    description=_(
        "Payment plugins call this endpoint in the return step of the "
        "payment flow. Depending on the plugin, either `GET` or `POST` "
        "is allowed as HTTP method.\n\nTypically payment plugins will "
        "redirect again to the URL where the SDK is embedded."
        "\n\nVarious validations are performed:"
        "\n* the form and submission must require payment"
        "\n* the `plugin_id` is configured on the form"
        "\n* payment is required and configured on the form"
        "\n* the redirect target must match the CORS policy"
    ),
    parameters=[
        OpenApiParameter(
            name="uuid",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("UUID identifying the payment."),
        ),
        OpenApiParameter(
            name="Location",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.URI,
            description=_("URL where the SDK initiated the payment flow."),
            response=[302],
            required=True,
        ),
        OpenApiParameter(
            name="Allow",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            description=_("Allowed HTTP method(s) for this plugin."),
            response=True,
            required=True,
        ),
    ],
    request=None,
    responses={
        302: OpenApiResponse(response=None, description=_("Tempomrary redirect")),
        (400, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Bad request. Invalid parameters were passed."),
        ),
        (404, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_(
                "Not found. The slug did not point to a live submission payment or "
                "the `plugin_id` does not exist."
            ),
        ),
    },
)
class PaymentReturnView(PaymentFlowBaseView, GenericAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    queryset = SubmissionPayment.objects.select_related("submission")
    parser_classes = (FormParser, MultiPartParser)

    def _handle_return(self, request, uuid: str):
        """
        Handle the return flow after the user provided payment credentials.

        This can be either directly to us, or via a payment plugin. This
        method essentially relays the django 'dispatch' to the relevant payment
        plugin. We must define ``get`` and ``post`` to have them properly show up and
        be documented in the OAS.

        TODO: check with Bart if we should wrap this in a transaction.atomic block
        or not - it depends on if the payment provider will re-deliver the webhook/return
        path if something goes wrong on our end.
        """
        payment = self.get_object()
        log = logger.bind(
            submission_uuid=str(payment.submission.uuid),
            payment_uuid=str(payment.uuid),
        )
        try:
            plugin = register[payment.plugin_id]
        except KeyError:
            raise NotFound(detail="unknown plugin")
        self._plugin = plugin
        log = log.bind(plugin=plugin)
        audit_log = audit_logger.bind(**structlog.get_context(log))

        if not payment.submission.payment_required:
            raise ParseError(detail="payment not required")

        if payment.plugin_id != payment.form.payment_backend:
            raise ParseError(detail="plugin not allowed")

        if plugin.return_method.upper() != request.method.upper():
            raise MethodNotAllowed(request.method)

        options = plugin.configuration_options(data=payment.plugin_options)
        try:
            options.is_valid(raise_exception=True)
            response = plugin.handle_return(request, payment, options.validated_data)
        except Exception as exc:
            audit_log.error("payment_flow_failure", exc_info=exc)
            raise
        else:
            audit_log.info("payment_flow_return")

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                log.warning(
                    "payment_return_blocked",
                    reason="disallowed_redirect",
                    status_code=response.status_code,
                    redirect_to=location,
                )
                raise ParseError(detail="redirect not allowed")

        payment.refresh_from_db()
        if payment.status == PaymentStatus.completed:
            transaction.on_commit(
                partial(
                    on_post_submission_event,
                    payment.submission.pk,
                    PostSubmissionEvents.on_payment_complete,
                )
            )

        return response

    def get(self, request, *args, **kwargs):
        return self._handle_return(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._handle_return(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override allowed methods from DRF APIView to use the plugin method.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        if hasattr(self, "_plugin"):
            response["Allow"] = self._plugin.return_method
        return response


@extend_schema(
    summary=_("Webhook handler for external payment flow"),
    description=_(
        "This endpoint is used for server-to-server calls. Depending on the plugin, multiple request "
        "HTTP methods are supported."
        "\n\nVarious validations are performed:"
        "\n* the `plugin_id` is configured on the form"
        "\n* payment is required and configured on the form"
        "\n\nWhenever the webhook_verification_header and webhook_verification_method"
        " settings are set for a plugin and a request has an empty request body,"
        " the request headers will be searched for the webhook_verification_header"
        " and will be returned as the response body."
    ),
    parameters=[
        OpenApiParameter(
            name="plugin_id",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_(
                "Identifier of the payment plugin. Note that this is validated "
                "against the configured available plugins for this particular form."
            ),
        ),
        OpenApiParameter(
            name="Allow",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            description=_("Allowed HTTP method(s) for this plugin."),
            response=True,
            required=True,
        ),
    ],
    request=None,
    responses={
        (status.HTTP_200_OK, "text/plain"): OpenApiResponse(
            response=str,
            examples=[
                OpenApiExample(
                    name="Webhook event",
                    value="",
                    media_type="text/plain",
                    status_codes=[status.HTTP_200_OK],
                    description=_(
                        "The response returned when a webhook event is processed."
                    ),
                ),
                OpenApiExample(
                    name="Verification header",
                    value="<verification-header-value>",
                    media_type="text/plain",
                    status_codes=[status.HTTP_200_OK],
                    description=_(
                        "The response returned when a verification header is set"
                        " and no request body is found."
                    ),
                ),
            ],
        ),
        (status.HTTP_400_BAD_REQUEST, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Bad request. Invalid parameters were passed."),
        ),
        (status.HTTP_404_NOT_FOUND, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Not found. The slug did not point to a live plugin."),
        ),
    },
)
class PaymentWebhookView(PaymentFlowBaseView):
    parser_classes = (
        FormParser,
        MultiPartParser,
        CamelCaseJSONParser,
        PlainTextParser,
    )

    def _handle_webhook(self, request, *args, **kwargs):
        try:
            plugin = register[kwargs["plugin_id"]]
        except KeyError:
            raise NotFound(detail="unknown plugin")
        self._plugin = plugin

        request_method = request.method.upper()

        if request_method not in plugin.allowed_http_methods:
            raise MethodNotAllowed(request.method)

        if (
            plugin.webhook_verification_header
            and request_method == plugin.webhook_verification_method
            and not request.body
        ):
            verification_value = request.headers.get(
                plugin.webhook_verification_header, ""
            )
            return HttpResponse(
                verification_value.encode("utf-8"),
                content_type="text/plain; charset=utf-8",
            )

        payment = plugin.handle_webhook(request)
        if payment:
            audit_logger.info(
                "payment_flow_webhook",
                submission_uuid=str(payment.submission.uuid),
                plugin=plugin,
                payment_uuid=str(payment.uuid),
            )
            if payment.status == PaymentStatus.completed:
                transaction.on_commit(
                    partial(
                        on_post_submission_event,
                        payment.submission.pk,
                        PostSubmissionEvents.on_payment_complete,
                    )
                )

        return HttpResponse(b"", content_type="text/plain")

    def get(self, request, *args, **kwargs):
        return self._handle_webhook(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._handle_webhook(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override allowed methods from DRF APIView to use the plugin method.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        if hasattr(self, "_plugin"):
            response["Allow"] = ", ".join(self._plugin.allowed_http_methods)
        return response


def hidden_form_for_data(data_dict):
    members = {
        key: forms.CharField(initial=value, widget=forms.HiddenInput)
        for key, value in data_dict.items()
    }
    return type("MyForm", (forms.Form,), members)


@method_decorator([never_cache], name="dispatch")
class PaymentLinkView(DetailView):
    template_name = "payments/payment_link.html"
    slug_url_kwarg = "uuid"
    slug_field = "uuid"
    queryset = Submission.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        submission = self.get_object()
        context["price"] = submission.price

        if submission.payment_required and not submission.payment_user_has_paid:
            plugin_id = submission.form.payment_backend
            plugin = register[plugin_id]
            payment = SubmissionPayment.objects.create_for(
                submission,
                plugin_id,
                submission.form.payment_backend_options,
                submission.price,
            )

            options = plugin.configuration_options(data=payment.plugin_options)
            options.is_valid(raise_exception=True)
            info = plugin.start_payment(self.request, payment, options.validated_data)
            audit_logger.info(
                "payment_flow_start",
                submission_uuid=str(payment.submission.uuid),
                plugin=plugin,
                payment_uuid=str(payment.uuid),
                from_email=True,
            )

            context["url"] = info.url
            context["method"] = info.type.upper()
            context["form"] = hidden_form_for_data(info.data)

        return context
