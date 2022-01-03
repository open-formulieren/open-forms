import logging

from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, serializers
from rest_framework.exceptions import MethodNotAllowed, NotFound, ParseError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.api.views import ERR_CONTENT_TYPE
from openforms.logging import logevent
from openforms.submissions.models import Submission
from openforms.utils.redirect import allow_redirect_url

from .api.serializers import PaymentInfoSerializer
from .models import SubmissionPayment
from .registry import register
from .tasks import update_submission_payment_status

logger = logging.getLogger(__name__)


class PaymentFlowBaseView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.Serializer


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
    queryset = Submission.objects.all()
    serializer_class = PaymentInfoSerializer

    def post(self, request, uuid: str, plugin_id: str):
        submission = self.get_object()
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

        info = plugin.start_payment(request, payment)
        logevent.payment_flow_start(payment, plugin)
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
    queryset = SubmissionPayment.objects.all()

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
        try:
            plugin = register[payment.plugin_id]
        except KeyError:
            raise NotFound(detail="unknown plugin")
        self._plugin = plugin

        if not payment.submission.payment_required:
            raise ParseError(detail="payment not required")

        if payment.plugin_id != payment.form.payment_backend:
            raise ParseError(detail="plugin not allowed")

        if plugin.return_method.upper() != request.method.upper():
            raise MethodNotAllowed(request.method)

        try:
            response = plugin.handle_return(request, payment)
        except Exception as e:
            logevent.payment_flow_failure(payment, plugin, e)
            raise
        else:
            logevent.payment_flow_return(payment, plugin)

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                logger.warning(
                    "blocked payment return with non-allowed redirect from "
                    "plugin '%(plugin_id)s' to '%(location)s'",
                    {"plugin_id": payment.plugin_id, "location": location},
                )
                raise ParseError(detail="redirect not allowed")

        transaction.on_commit(
            lambda: update_submission_payment_status.delay(payment.submission.id)
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
        "This endpoint is used for server-to-server calls. Depending on the plugin, either `GET` or `POST` "
        "is allowed as HTTP method."
        "\n\nVarious validations are performed:"
        "\n* the `plugin_id` is configured on the form"
        "\n* payment is required and configured on the form"
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
    responses={
        200: None,
        (400, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Bad request. Invalid parameters were passed."),
        ),
        (404, ERR_CONTENT_TYPE): OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Not found. The slug did not point to a live plugin."),
        ),
    },
)
class PaymentWebhookView(PaymentFlowBaseView):
    parser_classes = (FormParser, MultiPartParser)

    def _handle_webhook(self, request, *args, **kwargs):
        try:
            plugin = register[kwargs["plugin_id"]]
        except KeyError:
            raise NotFound(detail="unknown plugin")
        self._plugin = plugin

        if plugin.webhook_method.upper() != request.method.upper():
            raise MethodNotAllowed(request.method)

        payment = plugin.handle_webhook(request)
        if payment:
            logevent.payment_flow_webhook(payment, plugin)
            transaction.on_commit(
                lambda: update_submission_payment_status.delay(payment.submission.id)
            )

        return HttpResponse("")

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
            response["Allow"] = self._plugin.webhook_method
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

            info = plugin.start_payment(self.request, payment)

            context["url"] = info.url
            context["method"] = info.type.upper()
            context["form"] = hidden_form_for_data(info.data)

        return context
