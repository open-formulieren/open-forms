from copy import copy

from django.db import transaction
from django.utils.translation import gettext_lazy as _

import elasticapm
import structlog
from drf_spectacular.plumbing import build_array_type, build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from opentelemetry import trace
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.views import ListMixin
from openforms.formio.api.schema import FORMIO_COMPONENT_SCHEMA
from openforms.logging import audit_logger
from openforms.submissions.api.mixins import SubmissionCompletionMixin
from openforms.submissions.api.permissions import (
    ActiveSubmissionPermission,
    AnyActiveSubmissionPermission,
)
from openforms.submissions.models import Submission

from ..exceptions import AppointmentDeleteFailed, CancelAppointmentFailed
from ..models import Appointment, AppointmentsConfig
from ..utils import delete_appointment_for_submission, get_plugin
from .parsers import AppointmentCreateCamelCaseJSONParser
from .permissions import AppointmentCreatePermission
from .renderers import AppointmentCreateJSONRenderer
from .serializers import (
    AppointmentSerializer,
    CancelAppointmentInputSerializer,
    CustomerFieldsInputSerializer,
    DateInputSerializer,
    DateSerializer,
    LocationInputSerializer,
    LocationSerializer,
    PermissionSerializer,
    ProductInputSerializer,
    ProductSerializer,
    TimeInputSerializer,
    TimeSerializer,
)

tracer = trace.get_tracer("openforms.appointments.api.views")
# TODO: see openforms.validations.api.serializers.ValidatorsFilterSerializer.as_openapi_params
# and https://github.com/open-formulieren/open-forms/issues/611

PRODUCT_QUERY_PARAMETER = OpenApiParameter(
    name="product_id",
    type=build_array_type(build_basic_type(str), min_length=1),
    location=OpenApiParameter.QUERY,
    description=_("ID of the product, repeat for multiple products."),
    required=True,
    style="form",
    explode=True,
)
OPTIONAL_PRODUCT_QUERY_PARAMETER = copy(PRODUCT_QUERY_PARAMETER)
OPTIONAL_PRODUCT_QUERY_PARAMETER.required = False

LOCATION_QUERY_PARAMETER = OpenApiParameter(
    "location_id",
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    description=_("ID of the location"),
    required=True,
)


@extend_schema(
    summary=_("List available products"),
    parameters=[OPTIONAL_PRODUCT_QUERY_PARAMETER],
)
class ProductsListView(ListMixin, APIView):
    """
    List all products a user can choose when making an appointment.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = ProductSerializer

    def get_objects(self):
        serializer = ProductInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        plugin = get_plugin()
        config = AppointmentsConfig().get_solo()
        kwargs = {}
        if location_id := config.limit_to_location:
            kwargs["location_id"] = location_id

        if products := serializer.validated_data.get("product_id"):
            kwargs["current_products"] = products

        with (
            structlog.contextvars.bound_contextvars(
                action="appointments.get_available_products",
                plugin=plugin,
                location_id=location_id,
                current_products=products,
            ),
            tracer.start_as_current_span(
                name="get-available-products",
                attributes={
                    "span.type": "app",
                    "span.subtype": "appointments",
                    "span.action": "get_products",
                },
            ),
            elasticapm.capture_span(
                name="get-available-products",
                span_type="app.appointments.get_products",
            ),
        ):
            return plugin.get_available_products(**kwargs)


@extend_schema(
    summary=_("List available locations for a given product"),
    parameters=[PRODUCT_QUERY_PARAMETER],
)
class LocationsListView(ListMixin, APIView):
    """
    List all locations for a given product.

    Note that you must include valid querystring parameters to get actual results. If
    you don't, then an empty list is returned.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = LocationSerializer

    def get_objects(self):
        serializer = LocationInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        products = serializer.validated_data["product_id"]
        plugin = get_plugin()

        with (
            structlog.contextvars.bound_contextvars(
                action="appointments.get_locations",
                plugin=plugin,
                products=products,
            ),
            tracer.start_as_current_span(
                name="get-available-locations",
                attributes={
                    "span.type": "app",
                    "span.subtype": "appointments",
                    "span.action": "get_locations",
                },
            ),
            elasticapm.capture_span(
                name="get-available-locations",
                span_type="app.appointments.get_locations",
            ),
        ):
            return plugin.get_locations(products)


@extend_schema(
    summary=_("List available dates for a given location and product"),
    parameters=[
        PRODUCT_QUERY_PARAMETER,
        LOCATION_QUERY_PARAMETER,
    ],
)
class DatesListView(ListMixin, APIView):
    """
    List all dates for a given product.

    Note that you must include valid querystring parameters to get actual results. If
    you don't, then an empty list is returned.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = DateSerializer

    def get_objects(self):
        serializer = DateInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        products = serializer.validated_data["product_id"]
        location = serializer.validated_data["location_id"]

        plugin = get_plugin()

        with (
            structlog.contextvars.bound_contextvars(
                action="appointments.get_dates",
                plugin=plugin,
                products=products,
                location=location,
            ),
            tracer.start_as_current_span(
                name="get-available-dates",
                attributes={
                    "span.type": "app",
                    "span.subtype": "appointments",
                    "span.action": "get_dates",
                },
            ),
            elasticapm.capture_span(
                name="get-available-dates", span_type="app.appointments.get_dates"
            ),
        ):
            dates = plugin.get_dates(products, location)
        return [{"date": date} for date in dates]


@extend_schema(
    summary=_("List available times for a given location, product, and date"),
    parameters=[
        PRODUCT_QUERY_PARAMETER,
        LOCATION_QUERY_PARAMETER,
        OpenApiParameter(
            "date",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            description=_("The date"),
            required=True,
        ),
    ],
)
class TimesListView(ListMixin, APIView):
    """
    List all times for a given product.

    Note that you must include valid querystring parameters to get actual results. If
    you don't, then an empty list is returned.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = TimeSerializer

    def get_objects(self):
        serializer = TimeInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        products = serializer.validated_data["product_id"]
        location = serializer.validated_data["location_id"]
        date = serializer.validated_data["date"]

        plugin = get_plugin()

        with (
            structlog.contextvars.bound_contextvars(
                action="appointments.get_times",
                plugin=plugin,
                products=products,
                location=location,
                date=date,
            ),
            tracer.start_as_current_span(
                name="get-available-times",
                attributes={
                    "span.type": "app",
                    "span.subtype": "appointments",
                    "span.action": "get_times",
                },
            ),
            elasticapm.capture_span(
                name="get-available-times", span_type="app.appointments.get_times"
            ),
        ):
            times = plugin.get_times(products, location, date)
        return [{"time": time} for time in times]


@extend_schema(
    summary=_("Get required customer field details for a given product"),
    parameters=[PRODUCT_QUERY_PARAMETER],
    responses={
        200: OpenApiResponse(
            response=build_array_type(FORMIO_COMPONENT_SCHEMA, min_length=1),
            description=_("Customer fields list as Form.io components."),
        ),
        400: OpenApiResponse(
            response=ValidationErrorSerializer,
            description=_("Invalid input parameters."),
        ),
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Insufficient permissions."),
        ),
    },
)
class RequiredCustomerFieldsListView(APIView):
    """
    Retrieve the customer fields required for the appointment.

    Note that this requires valid querystring parameters to get results. You will get
    an HTTP 400 on invalid input parameters.

    The required fields are returned as a tuple of Form.io component definitions,
    with ready to use component keys, labels and relevant validators and an array of
    specific group fields rules or None.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    def get(self, request, *args, **kwargs):
        input_serializer = CustomerFieldsInputSerializer(data=self.request.query_params)
        input_serializer.is_valid(raise_exception=True)

        products = input_serializer.validated_data["product_id"]
        plugin = get_plugin()

        with (
            structlog.contextvars.bound_contextvars(
                action="appointments.get_required_customer_fields",
                plugin=plugin,
                products=products,
            ),
            tracer.start_as_current_span(
                name="get-required-customer-fields",
                attributes={
                    "span.type": "app",
                    "span.subtype": "appointments",
                    "span.action": "get_required_customer_fields",
                },
            ),
            elasticapm.capture_span(
                name="get-required-customer-fields",
                span_type="app.appointments.get_required_customer_fields",
            ),
        ):
            fields, required_group_fields = plugin.get_required_customer_fields(
                products
            )

        return Response(fields)


@extend_schema(
    summary=_("Cancel an appointment"),
    request=CancelAppointmentInputSerializer,
    responses={
        204: None,
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to verify ownership of the appointment."),
        ),
        502: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to cancel appointment."),
        ),
    },
)
class CancelAppointmentView(GenericAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "submission_uuid"
    queryset = Submission.objects.all()
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [ActiveSubmissionPermission]

    def post(self, request, *args, **kwargs):
        submission = self.get_object()
        plugin = get_plugin()

        with structlog.contextvars.bound_contextvars(
            action="appointments.cancel",
            plugin=plugin,
            submission_uuid=str(submission.uuid),
        ):
            audit_logger.info("appointment_cancel_start")
            serializer = CancelAppointmentInputSerializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                audit_logger.warning("appointment_cancel_failure", exc_info=exc)
                raise

            emails = submission.get_email_confirmation_recipients(submission.data)

            # The user must enter the email address they used when creating
            # the appointment which we validate here
            if serializer.validated_data["email"] not in emails:
                exc = PermissionDenied
                audit_logger.warning("appointment_cancel_failure", exc_info=exc)
                raise exc

            try:
                delete_appointment_for_submission(submission, plugin)
            except AppointmentDeleteFailed as exc:
                raise CancelAppointmentFailed() from exc

        return Response(status=HTTP_204_NO_CONTENT)


@extend_schema(
    summary=_("Create an appointment"),
    responses={
        201: AppointmentSerializer,
        400: OpenApiResponse(
            response=ValidationErrorSerializer,
            description=_("Invalid submission data."),
        ),
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Invalid or missing submission in session."),
        ),
        "5XX": OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to cancel appointment."),
        ),
    },
)
class CreateAppointmentView(SubmissionCompletionMixin, CreateAPIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [AnyActiveSubmissionPermission, AppointmentCreatePermission]
    serializer_class = AppointmentSerializer
    parser_classes = [AppointmentCreateCamelCaseJSONParser]
    renderer_classes = [AppointmentCreateJSONRenderer]

    _submission: Submission | None

    def extract_submission(self) -> Submission | None:
        if not hasattr(self, "_submission"):
            serializer = PermissionSerializer(data=self.request.data)
            if not serializer.is_valid():
                self._submission = None
            else:
                self._submission = serializer.validated_data["submission"]
        return self._submission

    def get_serializer_context(self):
        context = super().get_serializer_context()
        submission = self.extract_submission()
        context.update({"submission": submission})
        return context

    @transaction.atomic
    def create(self, request: Request, *args, **kwargs):
        # ensure any previous attempts are deleted before creating a new one
        submission = self.extract_submission()
        with structlog.contextvars.bound_contextvars(
            action="appointments.create",
            submission_uuid=str(submission.uuid) if submission else None,
        ):
            Appointment.objects.filter(submission=submission).delete()
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: AppointmentSerializer):
        super().perform_create(serializer)

        appointment: Appointment = serializer.instance  # type: ignore

        status_url = self._complete_submission(appointment.submission)
        # set the attribute so the response serializer can emit the status URL again
        serializer._status_url = status_url
