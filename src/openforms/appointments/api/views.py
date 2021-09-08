import logging

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.config.models import GlobalConfiguration
from openforms.submissions.api.permissions import (
    ActiveSubmissionPermission,
    AnyActiveSubmissionPermission,
)
from openforms.submissions.models import Submission
from openforms.submissions.utils import add_submmission_to_session
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
from ..tokens import submission_appointment_token_generator
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
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = LocationSerializer

    def get_objects(self):
        serializer = LocationInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

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
    List all locations for a given product.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = DateSerializer

    def get_objects(self):
        serializer = DateInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

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
    List all locations for a given product.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = TimeSerializer

    def get_objects(self):
        serializer = TimeInputSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

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
    summary=_("Verify the appointment cancel link."),
    responses={
        302: None,
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to verify token."),
        ),
        404: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to find submission."),
        ),
    },
)
class VerifyCancelAppointmentLinkView(RedirectView):

    permission_classes = ()
    authentication_classes = ()

    def get_redirect_url(
        self, base64_submission_uuid: int, token: str, *args, **kwargs
    ):
        submission_uuid = urlsafe_base64_decode(base64_submission_uuid).decode()

        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except ObjectDoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Cancel url is not valid")

        # Check that the token is valid
        valid = submission_appointment_token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
            raise PermissionDenied("Cancel url is not valid")

        add_submmission_to_session(submission, self.request.session)

        config = GlobalConfiguration.get_solo()

        # Displayed to user in SDK
        time = submission.appointment_info.start_time.isoformat()

        return f"{config.cancel_appointment_page}?time={time}&submission_uuid={str(submission_uuid)}"


@extend_schema(
    summary=_("Cancel an appointment"),
    responses={
        204: None,
        400: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to cancel appointment with given data."),
        ),
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to verify ownership of the appointment."),
        ),
    },
)
class CancelAppointmentView(RetrieveAPIView):
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

        if serializer.validated_data["email"] not in emails:
            raise PermissionDenied

        client = get_client()

        try:
            client.delete_appointment(submission.appointment_info.appointment_id)
            submission.appointment_info.cancel()
        except (AppointmentDeleteFailed, AppointmentInfo.DoesNotExist):
            raise CancelAppointmentFailed

        return Response(status=HTTP_204_NO_CONTENT)
