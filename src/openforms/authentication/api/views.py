from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...utils.api.views import ListMixin
from ..registry import register
from .serializers import AuthPluginSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available authentication plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all authentication plugins that have been registered.

    Each authentication plugin is tied to a particular (third-party) authentication
    provider. An authentication plugin usually provides a particular authentication
    attribute, such as the ``BSN`` or Chamber of Commerce number. A plugin may provide
    zero, one or multiple authentication attributes.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AuthPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


class AuthenticationLogoutView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular

    @extend_schema(
        summary=_("Delete session"),
        description=_(
            "Calling this endpoint will clear the current user session and delete the session cookie."
        ),
    )
    def delete(self, request, *args, **kwargs):
        request.session.flush()
        return Response(status=status.HTTP_204_NO_CONTENT)
