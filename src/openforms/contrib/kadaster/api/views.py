import logging

from django.contrib.gis.geos import fromstr
from django.utils.translation import gettext_lazy as _

import requests
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from zds_client import ClientError

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.views.mixins import ListMixin
from openforms.contrib.kadaster.models import KadasterApiConfig
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from .serializers import MapSearchSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    summary=_("List BAG address suggestions."),
    parameters=[
        OpenApiParameter(
            "q",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description=_("The search query we send to the pdok locatieserver api."),
            required=True,
        )
    ],
    responses={
        200: MapSearchSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        status.HTTP_403_FORBIDDEN: ExceptionSerializer,
    },
)
class MapSearchView(ListMixin, APIView):
    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = MapSearchSerializer

    def get_objects(self):
        config = KadasterApiConfig.get_solo()
        if not config.kadaster_service:
            raise ValidationError(
                {"invalid_params": _("No service defined for the Kadaster service.")}
            )

        query = self.request.GET.get("q")
        if not query:
            raise ValidationError({"invalid_params": _("Missing query parameter 'q'")})

        kadaster_client = config.kadaster_service.build_client()
        query_params = {"q": f"{query}"}

        bag_response = dict()
        try:
            bag_response = kadaster_client.operation(
                operation_id="free",
                data=None,
                url="v3_1/free",
                method="GET",
                request_kwargs=dict(
                    params=query_params,
                ),
            )
        except (ClientError, requests.RequestException):
            logger.exception("couldn't retrieve pdok locatieserver data")

        if not (
            (response := bag_response.get("response"))
            and (docs := response.get("docs"))
        ):
            # no response with docs: return empty
            return []

        def parse_doc(doc: dict) -> dict | None:
            """Parse a doc from pdok response into location"""
            try:
                lng, lat = fromstr(doc.get("centroide_ll"))
            except (ValueError, TypeError):
                logger.info(
                    f"Malformed centroide_ll in pdok locatieserver response: {doc}"
                )
                return

            try:
                x, y = fromstr(doc.get("centroide_rd"))
            except (ValueError, TypeError):
                logger.info(
                    f"Malformed centroide_rd in pdok locatieserver response: {doc}"
                )
                return

            return {
                "label": doc.get("weergavenaam", ""),
                "latLng": {"lat": lat, "lng": lng},
                "rd": {"x": x, "y": y},
            }

        locations = [loc for doc in docs if (loc := parse_doc(doc))]

        serializer = MapSearchSerializer(data=locations, many=True)
        if not serializer.is_valid(raise_exception=False):
            return []

        return serializer.validated_data
