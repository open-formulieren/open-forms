from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AnalyticsToolsConfiguration
from .serializers import AnalyticsToolsConfigSerializer


@extend_schema(
    summary=_("Analytics Tools Configuration"),
    description=_(
        "Returns information about the the analytics tools that are needed by the frontend."
    ),
    responses={200: AnalyticsToolsConfigSerializer},
)
class AnalyticsToolsConfigurationView(APIView):
    def get(self, request: Request) -> Response:
        conf = AnalyticsToolsConfiguration.get_solo()
        assert isinstance(conf, AnalyticsToolsConfiguration)

        serializer = AnalyticsToolsConfigSerializer(
            instance=conf, context={"request": request, "view": self}
        )

        return Response(serializer.data)
