from rest_framework import permissions, viewsets

from ..models import Theme
from .serializers import ThemeSerializer


class ThemeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Theme.objects.order_by("name")
    serializer_class = ThemeSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None  # we do not expect excessive amounts of themes
    lookup_field = "uuid"
