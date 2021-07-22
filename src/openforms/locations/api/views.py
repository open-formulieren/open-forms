from django.conf import settings
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


class GetStreetNameAndCityView(APIView):
    """
    Get the street name and city when given a postcode and house number
    """

    authentication_classes = ()

    @extend_schema(
        operation_id="get_street_name_and_city_list",
        summary=_("Get a street name and city"),
        description=_(
            "Get the street name and city for a given postcode and house number"
        ),
        request=GetStreetNameAndCityViewInputSerializer,
        responses=GetStreetNameAndCityViewResultSerializer,
        parameters=[
            OpenApiParameter(
                "postcode",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=_("Postcode of the address"),
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
        serializer = GetStreetNameAndCityViewInputSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        address_data = import_string(settings.OPENFORMS_LOCATION_CLIENT).get_address(
            data["postcode"], data["house_number"]
        )

        if not address_data:
            # If address is not found just return an empty response
            return Response({})

        return Response(GetStreetNameAndCityViewResultSerializer(address_data).data)
