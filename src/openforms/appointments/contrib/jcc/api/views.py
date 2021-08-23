from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from openforms.appointments.contrib.base import AppointmentLocation, AppointmentProduct
from openforms.appointments.contrib.jcc.api.tests.serializers import (
    DateInputSerializer,
    LocationInputSerializer,
    LocationSerializer,
    ProductSerializer,
    TimeInputSerializer,
)
from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission
from openforms.utils.api.views import ListMixin


@extend_schema_view(
    get=extend_schema(summary=_("List available JCC products")),
)
class ProductsListView(ListMixin, APIView):
    """
    List all products a user can choose when making an appointment.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = ProductSerializer

    def get_objects(self):
        config = JccConfig.get_solo()
        client = config.get_client()
        return client.get_available_products()


@extend_schema_view(
    get=extend_schema(summary=_("List available JCC locations for a given product")),
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

        config = JccConfig.get_solo()
        client = config.get_client()
        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )
        return client.get_locations([product])


@extend_schema_view(
    get=extend_schema(
        summary=_("List available dates for a given location and product")
    ),
)
class DatesListView(APIView):
    """
    List all locations for a given product.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    def get(self, request, *args, **kwargs):
        serializer = DateInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        config = JccConfig.get_solo()
        client = config.get_client()
        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )
        location = AppointmentLocation(
            identifier=serializer.validated_data["location_id"], name=""
        )
        return Response(status=HTTP_200_OK, data=client.get_dates([product], location))


@extend_schema_view(
    get=extend_schema(
        summary=_("List available times for a given location, product, and date")
    ),
)
class TimesListView(APIView):
    """
    List all locations for a given product.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    def get(self, request, *args, **kwargs):
        serializer = TimeInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        config = JccConfig.get_solo()
        client = config.get_client()
        product = AppointmentProduct(
            identifier=serializer.validated_data["product_id"], code="", name=""
        )
        location = AppointmentLocation(
            identifier=serializer.validated_data["location_id"], name=""
        )
        return Response(
            status=HTTP_200_OK,
            data=client.get_times(
                [product], location, serializer.validated_data["date"]
            ),
        )
