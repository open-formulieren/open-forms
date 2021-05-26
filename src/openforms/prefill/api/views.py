from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..registry import register
from .serializers import PluginSerializer


class PluginListView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PluginSerializer

    def get_serializer(self, **kwargs):
        return self.serializer_class(
            many=True,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        summary=_("List available prefill plugins"),
    )
    def get(self, request, *args, **kwargs):
        """
        List all prefill plugins that have been registered.
        """
        plugins = list(register)
        serializer = self.get_serializer(instance=plugins)
        return Response(serializer.data)
