from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FixedMetadataVariableSerializer


class FixedMetadataVariablesView(APIView):

    serializer_class = FixedMetadataVariableSerializer

    @extend_schema(
        summary=_("Fixed metadata variables JSON dump registration backend"),
        description=_(
            "Return a list of fixed metadata variables for the JSON dump registration "
            "backend that are needed by the frontend as default options."
        ),
    )
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(data={})
        serializer.is_valid()
        return Response(serializer.data["variables"])
