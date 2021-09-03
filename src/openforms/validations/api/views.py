from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.utils.api.views import ListMixin
from openforms.validations.api.serializers import (
    ValidationInputSerializer,
    ValidationPluginSerializer,
    ValidationResultSerializer,
)
from openforms.validations.registry import register


@extend_schema_view(
    get=extend_schema(summary=_("List available validation plugins")),
)
class ValidatorsListView(ListMixin, APIView):
    """
    List all prefill plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ValidationPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


class ValidationView(APIView):
    """
    Validate a value using given validator
    """

    authentication_classes = ()

    @extend_schema(
        operation_id="validation_run",
        summary=_("Validate value using validation plugin"),
        request=ValidationInputSerializer,
        responses=ValidationResultSerializer,
        parameters=[
            OpenApiParameter(
                "validator",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                enum=[validator.identifier for validator in register],
                description=_(
                    "ID of the validation plugin, see the [`validation_plugin_list`]"
                    "(./#operation/validation_plugin_list) operation"
                ),
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = ValidationInputSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        result = register.validate(self.kwargs["validator"], serializer.data["value"])
        return Response(ValidationResultSerializer(result).data)
