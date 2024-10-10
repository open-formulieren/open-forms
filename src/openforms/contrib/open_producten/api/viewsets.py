from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, viewsets

from openforms.products.models import Product as ProductType

from .serializers import ProductTypeSerializer


@extend_schema_view(
    list=extend_schema(
        summary=_("List available products with current price options"),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve details of a single product"),
    ),
)
class PriceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve the products registered in the admin interface.

    Note that these endpoints are only available to authenticated admin users. The
    products functionality is minimal to be able to register prices. In the future,
    probably a dedicated products catalogue will become relevant.
    """

    # queryset = ProductType.objects.all()
    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.TokenAuthentication,
    )
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ProductTypeSerializer
    lookup_field = "open_product_uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        return ProductType.objects.filter(
            open_producten_price__isnull=False, is_deleted=False
        ).distinct()
