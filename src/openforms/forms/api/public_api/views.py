from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView

from ...models import Form
from .filters import FormCategoryNameFilter
from .pagination import NoPagination
from .permissions import ViewFormPermission
from .serializers import FormSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("List forms"),
        description=_(
            "List the available forms with minimal information. Does not include soft deleted forms."
        ),
    ),
)
class FormListView(ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, ViewFormPermission)

    serializer_class = FormSerializer
    filterset_class = FormCategoryNameFilter
    queryset = Form.objects.filter(_is_deleted=False)
    pagination_class = NoPagination
