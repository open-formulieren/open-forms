from functools import partial

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.views.mixins import ListMixin
from openforms.contrib.kadaster.clients.bag import AddressResult
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..clients import get_bag_client, get_locatieserver_client
from .serializers import (
    AddressSearchResultSerializer,
    GetStreetNameAndCityViewInputSerializer,
    GetStreetNameAndCityViewResultSerializer,
    LatLngSearchInputSerializer,
    LatLngSearchResultSerializer,
)

ADDRESS_AUTOCOMPLETE_CACHE_TIMEOUT = (
    60 * 60 * 24
)  # 24 hours - address data does NOT update frequently


def lookup_address(postcode: str, number: str) -> AddressResult | None:
    with get_bag_client() as client:
        return client.get_address(postcode, number)


class AddressAutocompleteView(APIView):
    """
    Get the street name and city when given a postcode and house number.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    @extend_schema(
        summary=_("Get a street name and city"),  # type: ignore
        description=_(
            "Get the street name and city for a given postal code and house number."
        ),
        responses=GetStreetNameAndCityViewResultSerializer,
        parameters=[
            OpenApiParameter(
                "postcode",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=_("Postal code of the address"),  # type: ignore
                required=True,
            ),
            OpenApiParameter(
                "house_number",
                OpenApiTypes.NUMBER,
                OpenApiParameter.QUERY,
                description=_("House number of the address"),  # type: ignore
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        serializer = GetStreetNameAndCityViewInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        postcode, number = data["postcode"], data["house_number"]

        # check the cache so we avoid hitting the remote API too often (and risk
        # of being throttled, see #1832)
        address_data = cache.get_or_set(
            key=f"BAG|get_address|{postcode}|{number}",
            default=partial(lookup_address, postcode, number),
            timeout=ADDRESS_AUTOCOMPLETE_CACHE_TIMEOUT,
        )

        return Response(GetStreetNameAndCityViewResultSerializer(address_data).data)


@extend_schema(
    summary=_("Get an adress based on coordinates"),  # type: ignore
    description=_(
        "Get the closest address name based on the given longitude and latitude."
    ),  # type: ignore
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
    summary=_("List address suggestions with coordinates."),  # type: ignore
    description=_(
        "Get a list of addresses, ordered by relevance/match score of the input "
        "query. Note that only results having latitude/longitude data are returned.\n\n"
        "The results are retrieved from the configured geo search service, defaulting "
        "to the Kadaster location server."
    ),  # type: ignore
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
