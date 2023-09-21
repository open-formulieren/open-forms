import logging

from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.views.mixins import ListMixin
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..client import get_locatieserver_client
from .serializers import (
    AddressSearchResultSerializer,
    LatLngSearchInputSerializer,
    LatLngSearchResultSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    summary=_("Get an adress based on coordinates"),
    description=_(
        "Get the closest address name based on the given longitude and latitude."
    ),
    parameters=[
        OpenApiParameter(
            "lat",
            OpenApiTypes.FLOAT,
            OpenApiParameter.QUERY,
            description=_("The latitude of the location, in decimal degrees."),
            required=True,
        ),
        OpenApiParameter(
            "lng",
            OpenApiTypes.FLOAT,
            OpenApiParameter.QUERY,
            description=_("The longitude of the location, in decimal degrees."),
            required=True,
        ),
    ],
    responses={
        200: LatLngSearchResultSerializer,
        204: None,
        status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        status.HTTP_403_FORBIDDEN: ExceptionSerializer,
    },
)
class LatLngSearchView(APIView):
    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    def get(self, request: Request):
        input_serializer = LatLngSearchInputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        client = get_locatieserver_client()
        with client:
            label = client.reverse_address_search(
                input_serializer.validated_data["lat"],
                input_serializer.validated_data["lng"],
            )

        if not label:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = LatLngSearchResultSerializer(
            instance={"label": label},
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary=_("List address suggestions with coordinates."),
    description=_(
        "Get a list of addresses, ordered by relevance/match score of the input "
        "query. Note that only results having latitude/longitude data are returned.\n\n"
        "The results are retrieved from the configured geo search service, defaulting "
        "to the Kadaster location server."
    ),
    parameters=[
        OpenApiParameter(
            "q",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_(
                "Search query for the address to retrieve suggestions with geo-information for."
            ),
            required=True,
        )
    ],
    responses={
        200: AddressSearchResultSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        status.HTTP_403_FORBIDDEN: ExceptionSerializer,
    },
)
class AddressSearchView(ListMixin, APIView):
    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = AddressSearchResultSerializer

    def get_objects(self):
        # input validation
        if not (query := self.request.GET.get("q")):
            raise serializers.ValidationError(
                {"q": _("Missing query parameter 'q'")},
                code="required",
            )

        client = get_locatieserver_client()
        with client:
            return client.free_address_search(query)
