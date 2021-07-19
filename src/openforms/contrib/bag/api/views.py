from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.contrib.bag.api.serializers import (
    GetStreetNameAndCityViewInputSerializer,
    GetStreetNameAndCityViewResultSerializer,
)
from openforms.contrib.bag.models import BAGConfig


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
        config = BAGConfig.get_solo()
        client = config.bag_service.build_client()
        response = client.operation(
            "bevraagAdressen",
            {},
            method="GET",
            request_kwargs=dict(
                params=serializer.validated_data,
                headers={"Accept": "application/hal+json"},
            ),
        )

        return Response(
            GetStreetNameAndCityViewResultSerializer(
                response["_embedded"]["adressen"][0]
            ).data
        )
