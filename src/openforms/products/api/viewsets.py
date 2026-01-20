from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from openforms.products.models.price_option import PriceOption

from ..models import Product
from .serializers import PriceOptionSerializer, ProductSerializer


@extend_schema_view(
    list=extend_schema(
        summary=_("List available products"),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve details of a single product"),
    ),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve the products registered in the admin interface.

    Note that these endpoints are only available to authenticated admin users. The
    products functionality is minimal to be able to register prices. In the future,
    probably a dedicated products catalogue will become relevant.
    """

    queryset = Product.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ProductSerializer
    lookup_field = "uuid"


@extend_schema_view(
    list=extend_schema(
        summary=_("List available price options"),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve details of a single price option"),
    ),
)
class PriceOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve the price options of a product registered in the admin interface.

    Note that these endpoints are only available to authenticated admin users. The
    products functionality is minimal to be able to register prices.
    """

    queryset = PriceOption.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = PriceOptionSerializer
    lookup_field = "price_option_uuid"
