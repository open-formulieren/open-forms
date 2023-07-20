import logging
import re

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _

import requests
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
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
        200: MapSearchSerializer,
        status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
    },
)
class MapSearchView(GenericAPIView):
    serializer_class = MapSearchSerializer
    permission_classes = [AnyActiveSubmissionPermission]
    renderer_classes = [CamelCaseJSONRenderer]

    def get(self, request: Request, *args, **kwargs):
        query = request.GET.get("q")
        if not query:
            return HttpResponseBadRequest(_("Missing query parameter 'q'"))

        url = f"{settings.PDOK_LOCATIE_SERVER_URL}free"
        data = {"q": query}

        try:
            bag_data = requests.get(url, params=data)
        except requests.exceptions.RequestException as e:
            logger.exception(f"couldn't retrieve pdok locatieserver data: {e}")

        locations = []

        if not (
            (bag_data.status_code == status.HTTP_200_OK)
            and (response := bag_data.json().get("response"))
            and (docs := response.get("docs"))
        ):
            # no response with docs: return empty
            return Response(
                self.serializer_class(
                    instance=[],
                    context={"request": request},
                    many=True,
                ).data
            )

        def parse_doc(doc: dict) -> dict | None:
            """Parse a doc from pdok response into location"""
            try:
                lng, lat = re.findall(r"\d+\.\d+", doc.get("centroide_ll", ""))
            except ValueError:
                logger.info(
                    f"Malformed centroide_ll in pdok locatieserver response: {doc}"
                )
                return
            try:
                x, y = re.findall(r"\d+\.\d+", doc.get("centroide_rd", ""))
            except ValueError:
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
        return Response(
            self.serializer_class(
                instance=locations,
                context={"request": request},
                many=True,
            ).data
        )
