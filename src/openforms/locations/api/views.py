from functools import partial

from django.conf import settings
from django.core.cache import caches
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.locations.api.serializers import (
    GetStreetNameAndCityViewInputSerializer,
    GetStreetNameAndCityViewResultSerializer,
)
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours - address data does NOT update frequently


def lookup_address(postcode: str, number: str) -> dict:
    ClientCls = import_string(settings.OPENFORMS_LOCATION_CLIENT)
    return ClientCls.get_address(postcode, number)


class GetStreetNameAndCityView(APIView):
    """
    Get the street name and city when given a postcode and house number
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]

    @extend_schema(
        operation_id="get_street_name_and_city_list",
        summary=_("Get a street name and city"),
        description=_(
            "Get the street name and city for a given postal code and house number"
        ),
        responses=GetStreetNameAndCityViewResultSerializer,
        parameters=[
            OpenApiParameter(
                "postcode",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=_("Postal code of the address"),
                required=True,
            ),
            OpenApiParameter(
                "house_number",
                OpenApiTypes.NUMBER,
                OpenApiParameter.QUERY,
                description=_("House number of the address"),
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
        address_data = caches["default"].get_or_set(
            key=f"{settings.OPENFORMS_LOCATION_CLIENT}|{postcode}|{number}",
            default=partial(lookup_address, postcode, number),
            timeout=CACHE_TIMEOUT,
        )

        if not address_data:
            # If address is not found just return an empty response
            return Response({})

        return Response(GetStreetNameAndCityViewResultSerializer(address_data).data)
