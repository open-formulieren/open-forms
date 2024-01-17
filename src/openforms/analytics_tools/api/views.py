from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView

from ..models import AnalyticsToolsConfiguration
from .serializers import AnalyticsToolsConfigSerializer


@extend_schema(
    summary=_("Analytics Tools Configuration"),
    description=_(
        "Returns information about the analytics tools that are needed by the frontend."
    ),
    responses={200: AnalyticsToolsConfigSerializer},
)
class AnalyticsToolsConfigurationView(RetrieveAPIView):
    serializer_class = AnalyticsToolsConfigSerializer

    def get_object(self) -> AnalyticsToolsConfiguration:
        return AnalyticsToolsConfiguration.get_solo()
