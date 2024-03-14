from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer
from openforms.api.views import ListMixin
from openforms.forms.api.serializers import FormVariableSerializer
from openforms.registrations.registry import register as registration_plugins_registry

from ..service import get_static_variables
from .registration_serializer import RegistrationPluginVariablesSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("Get static variables"),
        description=_(
            "List the static variables that will be associated with every form"
        ),
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


@extend_schema_view(
    get=extend_schema(
        summary=_("Get registration static variables"),
        description=_(
            "List the registration static variables that will be associated with every form"
        ),
        responses={
            200: FormVariableSerializer(many=True),
            403: ExceptionSerializer,
        },
    ),
)
class RegistrationPluginVariablesView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, *args, **kwargs):
        serializer = RegistrationPluginVariablesSerializer(
            registration_plugins_registry.iter_enabled_plugins(), many=True
        )
        return Response(serializer.data)
