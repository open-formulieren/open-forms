import logging
from decimal import Decimal

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed

from rest_framework import permissions
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.payments.api.serializers import PaymentInfoSerializer
from openforms.payments.models import SubmissionPayment
from openforms.payments.registry import register
from openforms.submissions.models import Submission
from openforms.utils.redirect import allow_redirect_url

logger = logging.getLogger(__name__)


class PaymentFlowBaseView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    register = register


class PaymentStartView(RetrieveAPIView, PaymentFlowBaseView):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    queryset = Submission.objects.all()
    serializer_class = PaymentInfoSerializer

    def post(self, request, uuid: str, plugin_id: str):
        submission = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")

        if not submission.form.payment_required:
            return HttpResponseBadRequest("payment not required")

        if plugin_id != submission.form.payment_backend:
            return HttpResponseBadRequest("plugin not allowed")

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        if not allow_redirect_url(form_url):
            logger.warning(
                "blocked payment start with non-allowed redirect to '%(form_url)s'",
                {"form_url": form_url},
            )
            return HttpResponseBadRequest("redirect not allowed")

        payment = SubmissionPayment.objects.create_for(
            submission,
            plugin_id,
            # TODO pass amount from form
            Decimal(10),
            form_url,
            # options=submission.form.payment_options,
        )

        info = plugin.start_payment(request, payment)
        return Response(
            self.serializer_class(instance=info, context={"request": request}).data
        )


class PaymentReturnView(RetrieveAPIView, PaymentFlowBaseView):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    queryset = SubmissionPayment.objects.all()

    parser_classes = (FormParser, MultiPartParser)

    def _handle_return(self, request, uuid: str):
        """
        Handle the return flow after the user provided payment credentials.

        This can be either directly to us, or via an payment plugin. This
        method essentially relays the django 'dispatch' to the relevant payment
        plugin. We must define ``get`` and ``post`` to have them properly show up and
        be documented in the OAS.
        """
        payment = self.get_object()
        try:
            plugin = self.register[payment.plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")
        self._plugin = plugin

        if not payment.form.payment_required:
            return HttpResponseBadRequest("payment not required")

        if payment.plugin_id != payment.form.payment_backend:
            return HttpResponseBadRequest("plugin not allowed")

        if plugin.return_method.upper() != request.method.upper():
            return HttpResponseNotAllowed([plugin.return_method])

        response = plugin.handle_return(request, payment)

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                logger.warning(
                    "blocked payment return with non-allowed redirect from "
                    "plugin '%(plugin_id)s' to '%(location)s'",
                    {"plugin_id": payment.plugin_id, "location": location},
                )
                return HttpResponseBadRequest("redirect not allowed")

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


class PaymentWebhookView(PaymentFlowBaseView):
    register = register
    parser_classes = (FormParser, MultiPartParser)

    def _handle_webhook(self, request, *args, **kwargs):
        try:
            plugin = self.register[kwargs["plugin_id"]]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")
        self._plugin = plugin

        if plugin.webhook_method.upper() != request.method.upper():
            return HttpResponseNotAllowed([plugin.webhook_method])

        plugin.handle_webhook(request)
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
