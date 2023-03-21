from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.api.views import ListMixin
from openforms.forms.api.serializers import FormVariableSerializer

from ..service import get_static_variables


@extend_schema_view(
    get=extend_schema(
        summary=_("Get static data"),
        description=_("List the static data that will be associated with every form"),
        responses={
            200: FormVariableSerializer(many=True),
            403: ExceptionSerializer,
        },
    ),
)
class StaticFormVariablesView(ListMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = FormVariableSerializer

    def get_objects(self):
        return get_static_variables()
