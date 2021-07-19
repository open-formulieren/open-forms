from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.contrib.bag.models import BAGConfig
from openforms.locations.api.serializers import (
    GetStreetNameAndCityViewInputSerializer,
    GetStreetNameAndCityViewResultSerializer,
)


class GetStreetNameAndCityView(APIView):
    """
    Validate a value using given validator
    """

    authentication_classes = ()

    @extend_schema(
        operation_id="street_name_and_city",
        summary=_("Validate value using validation plugin"),
        request=GetStreetNameAndCityViewInputSerializer,
        responses=GetStreetNameAndCityViewResultSerializer,
        parameters=[
            OpenApiParameter(
                "Street Name and City",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description=_(
                    "Get Street Name and City by passing in Postcode and House Number"
                ),
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        serializer = GetStreetNameAndCityViewInputSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        # Make API request to BAG here
        # TODO Move this out of this function
        #  Think of how different backends were implements in Open Personen
        config = BAGConfig.get_solo()
        client = config.bag_service.build_client()
        data = serializer.validated_data
        data["huisnummer"] = data.pop("house_number")
        response = client.operation(
            "bevraagAdressen",
            {},
            method="GET",
            request_kwargs=dict(
                params=data,
                headers={"Accept": "application/hal+json"},
            ),
        )
        address_data = response["_embedded"]["adressen"][0]
        address_data["street_name"] = address_data.pop("korteNaam")
        address_data["city"] = address_data.pop("woonplaatsNaam")

        return Response(GetStreetNameAndCityViewResultSerializer(address_data).data)
