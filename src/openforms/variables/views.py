from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.forms.api.serializers import FormVariableSerializer
from openforms.forms.models import FormVariable
from openforms.utils.api.views import ListMixin


@extend_schema_view(
    get=extend_schema(
        summary=_("Get static form variables"),
        description=_("List the static form variables that every form should have"),
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
    renderer_classes = [JSONRenderer]

    def get_objects(self):
        return FormVariable.get_default_static_variables()
