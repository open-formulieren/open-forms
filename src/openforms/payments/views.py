import logging
from decimal import Decimal

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, serializers
from rest_framework.exceptions import MethodNotAllowed, NotFound, ParseError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.payments.api.serializers import PaymentInfoSerializer
from openforms.payments.models import SubmissionPayment
from openforms.payments.registry import register
from openforms.payments.services import update_submission_payment_registration
from openforms.submissions.models import Submission
from openforms.utils.redirect import allow_redirect_url

logger = logging.getLogger(__name__)


class PaymentFlowBaseView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.Serializer


@extend_schema(
    summary=_("Start payment flow"),
    description=_(
        "This endpoint provides information to start external login flow for a submission."
        "\n\nDue to support for legacy platforms this view doesn't redirect but provides information for the frontend to be used client side."
        "\n\nVarious validations are performed:"
        "\n* the form and submission must require payment"
        "\n* the `plugin_id` is configured on the form"
        "\n* payment is required and configured on the form"
        "\n* the `next` parameter must be present"
        "\n* the `next` parameter must match the CORS policy"
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
    responses={
        (200, "application/json"): OpenApiResponse(
            response=PaymentInfoSerializer,
            description=_(
                "Depending on the 'type' send a GET or POST request with the 'data' as Form Data to given 'url'."
            ),
        ),
        (400, "text/html"): OpenApiResponse(
            response=str, description=_("Bad request. Invalid parameters were passed.")
        ),
        (404, "text/html"): OpenApiResponse(
            response=str,
            description=_("Not found. The slug did not point to a live submission."),
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

        if plugin_id != submission.form.payment_backend:
            raise ParseError(detail="plugin not allowed")

        form_url = request.GET.get("next")
        if not form_url:
            raise ParseError(detail="missing 'next' parameter")

        if not allow_redirect_url(form_url):
            logger.warning(
                "blocked payment start with non-allowed redirect to '%(form_url)s'",
                {"form_url": form_url},
            )
            raise ParseError(detail="redirect not allowed")

        payment = SubmissionPayment.objects.create_for(
            submission,
            plugin_id,
            submission.form.payment_backend_options,
            submission.form.product.price,
            form_url,
        )

        info = plugin.start_payment(request, payment)
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
            description=_("URL where the SDK initiated the authentication flow."),
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
        302: None,
        (400, "text/html"): OpenApiResponse(
            response=str, description=_("Bad request. Invalid parameters were passed.")
        ),
        (404, "text/html"): OpenApiResponse(
            response=str,
            description=_("Not found. The slug did not point to a live form."),
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

        response = plugin.handle_return(request, payment)

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                logger.warning(
                    "blocked payment return with non-allowed redirect from "
                    "plugin '%(plugin_id)s' to '%(location)s'",
                    {"plugin_id": payment.plugin_id, "location": location},
                )
                raise ParseError(detail="redirect not allowed")

        update_submission_payment_registration(payment.submission)

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
        (400, "text/html"): OpenApiResponse(
            response=str, description=_("Bad request. Invalid parameters were passed.")
        ),
        (404, "text/html"): OpenApiResponse(
            response=str,
            description=_("Not found. The slug did not point to a live plugin."),
        ),
    },
)
class PaymentWebhookView(PaymentFlowBaseView):
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
            update_submission_payment_registration(payment.submission)

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
