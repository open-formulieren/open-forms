from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin

from ..models import AttributeGroup
from .serializers import AttributeGroupSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available Yivi attribute groups")),
)
class AttributeGroupListView(ListModelMixin, GenericAPIView):
    """
    List all Yivi attribute groups.

    The attribute groups are used during Yivi authentication. They allow greater levels
    of authentication customization, by per form definition of authentication attributes.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AttributeGroupSerializer
    queryset = AttributeGroup.objects.all()
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
