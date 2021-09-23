import logging

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.submissions.api.permissions import (
    ActiveSubmissionPermission,
    AnyActiveSubmissionPermission,
)
from openforms.submissions.models import Submission
from openforms.utils.api.views import ListMixin

from ..api.serializers import (
    CancelAppointmentInputSerializer,
    DateInputSerializer,
    DateSerializer,
    LocationInputSerializer,
    LocationSerializer,
    ProductSerializer,
    TimeInputSerializer,
    TimeSerializer,
)
from ..base import AppointmentLocation, AppointmentProduct
from ..exceptions import AppointmentDeleteFailed, CancelAppointmentFailed
from ..models import AppointmentInfo
from ..utils import get_client

logger = logging.getLogger(__name__)


@extend_schema(
    summary=_("List available products"),
)
class ProductsListView(ListMixin, APIView):
    """
    List all products a user can choose when making an appointment.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = ProductSerializer

    def get_objects(self):
        client = get_client()
        return client.get_available_products()


# The serializer + @extend_schema approach for querystring params is not ideal, the
# issue to refactor this is here: https://github.com/open-formulieren/open-forms/issues/611
@extend_schema(
    summary=_("List available locations for a given product"),
    parameters=[
        OpenApiParameter(
            "product_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("ID of the product"),
            required=True,
        ),
    ],
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
        is_valid = serializer.is_valid()
        # TODO: ideally we want to use raise_exception=True, but the SDK and the way
        # that Formio work is that we can't prevent the invalid request from firing.
        # Instead, we just return an empty result list which populates dropdowns with
        # empty options.
        if not is_valid:
            return []

        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )

        client = get_client()
        return client.get_locations([product])


@extend_schema(
    summary=_("List available dates for a given location and product"),
    parameters=[
        OpenApiParameter(
            "product_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("ID of the product"),
            required=True,
        ),
        OpenApiParameter(
            "location_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("ID of the location"),
            required=True,
        ),
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
        is_valid = serializer.is_valid()
        # TODO: ideally we want to use raise_exception=True, but the SDK and the way
        # that Formio work is that we can't prevent the invalid request from firing.
        # Instead, we just return an empty result list which populates dropdowns with
        # empty options.
        if not is_valid:
            return []

        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )
        location = AppointmentLocation(
            identifier=serializer.validated_data["location_id"], name=""
        )

        client = get_client()
        dates = client.get_dates([product], location)
        return [{"date": date} for date in dates]


@extend_schema(
    summary=_("List available times for a given location, product, and date"),
    parameters=[
        OpenApiParameter(
            "product_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("ID of the product"),
            required=True,
        ),
        OpenApiParameter(
            "location_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("ID of the location"),
            required=True,
        ),
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
        is_valid = serializer.is_valid()
        # TODO: ideally we want to use raise_exception=True, but the SDK and the way
        # that Formio work is that we can't prevent the invalid request from firing.
        # Instead, we just return an empty result list which populates dropdowns with
        # empty options.
        if not is_valid:
            return []

        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )
        location = AppointmentLocation(
            identifier=serializer.validated_data["location_id"], name=""
        )

        client = get_client()
        times = client.get_times([product], location, serializer.validated_data["date"])
        return [{"time": time} for time in times]


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
    authentication_classes = ()
    permission_classes = [ActiveSubmissionPermission]

    def post(self, request, *args, **kwargs):
        submission = self.get_object()

        serializer = CancelAppointmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emails = submission.get_email_confirmation_recipients(submission.data)

        # The user must enter the email address they used when creating
        #   the appointment which we validate here
        if serializer.validated_data["email"] not in emails:
            raise PermissionDenied

        client = get_client()

        try:
            client.delete_appointment(submission.appointment_info.appointment_id)
            submission.appointment_info.cancel()
        except (AppointmentDeleteFailed, AppointmentInfo.DoesNotExist):
            raise CancelAppointmentFailed

        return Response(status=HTTP_204_NO_CONTENT)
