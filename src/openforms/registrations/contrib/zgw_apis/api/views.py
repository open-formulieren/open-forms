from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view

from openforms.contrib.zgw.api.views import (
    BaseCatalogiListView,
    BaseInformatieObjectTypenListView,
)

from .filters import (
    APIGroupQueryParamsSerializer,
    ListInformatieObjectTypenQueryParamsSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List the available Catalogi from the provided ZGW API group"),
        parameters=[APIGroupQueryParamsSerializer],
    ),
)
class CatalogiListView(BaseCatalogiListView):
    filter_serializer_class = APIGroupQueryParamsSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_(
            "List the available InformatieObjectTypen from the provided ZGW API group"
        ),
        parameters=[ListInformatieObjectTypenQueryParamsSerializer],
    ),
)
class InformatieObjectTypenListView(BaseInformatieObjectTypenListView):
    filter_serializer_class = ListInformatieObjectTypenQueryParamsSerializer
