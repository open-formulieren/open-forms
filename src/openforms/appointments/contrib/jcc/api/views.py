from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from openforms.appointments.contrib.jcc.api.tests.serializers import ProductSerializer
from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission
from openforms.utils.api.views import ListMixin


@extend_schema_view(
    get=extend_schema(summary=_("List available JCC products")),
)
class ProductsListView(ListMixin, APIView):
    """
    List all prefill plugins that have been registered.
    """

    authentication_classes = ()
    permission_classes = [AnyActiveSubmissionPermission]
    serializer_class = ProductSerializer

    def get_objects(self):
        config = JccConfig.get_solo()
        client = config.get_client()
        return client.get_available_products()
