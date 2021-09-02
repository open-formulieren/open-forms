from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from openforms.submissions.api.permissions import AnyActiveSubmissionPermission
from openforms.utils.api.views import ListMixin

from ..api.serializers import (
    DateInputSerializer,
    DateSerializer,
    LocationInputSerializer,
    LocationSerializer,
    ProductSerializer,
    TimeInputSerializer,
    TimeSerializer,
)
from ..base import AppointmentLocation, AppointmentProduct
from ..utils import get_client


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
            description=_("Id of the product"),
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
            description=_("Id of the product"),
            required=True,
        ),
        OpenApiParameter(
            "location_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("Id of the location"),
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
            description=_("Id of the product"),
            required=True,
        ),
        OpenApiParameter(
            "location_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("Id of the location"),
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
