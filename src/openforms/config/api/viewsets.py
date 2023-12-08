from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from ..models import Theme
from .serializers import ThemeSerializer


@extend_schema_view(
    list=extend_schema(summary=_("List available themes")),
    retrieve=extend_schema(summary=_("Retrieve theme details")),
)
class ThemeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Obtain information about the configured themes.

    A theme is a collection of styling/appearance related configuration. Themes are
    configured and managed in the admin interface.

    When designing forms, you can optionally specify which theme to use for that
    particular form.

    You must have staff permissions to be able to use the theme endpoints.
    """

    queryset = Theme.objects.order_by("name")
    serializer_class = ThemeSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None  # we do not expect excessive amounts of themes
    lookup_field = "uuid"
