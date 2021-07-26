from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from ...utils.api.views import ListMixin
from ..registry import register
from .serializers import PaymentPluginSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available payment plugins")),
)
class PaymentPluginListView(ListMixin, APIView):
    """
    List all payment plugins that have been registered.

    Each payment plugin is tied to a particular (third-party) payment
    provider.
    """

    payment_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PaymentPluginSerializer

    def get_objects(self):
        return list(register)
