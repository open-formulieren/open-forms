from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.validations.api.serializers import (
    ValidationInputSerializer,
    ValidationPluginSerializer,
    ValidationResultSerializer,
)
from openforms.validations.registry import register
from django.views.decorators.csrf import csrf_exempt


class ValidatorsListView(APIView):
    """
    List all prefill plugins that have been registered.
    """

    register = register

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ValidationPluginSerializer

    def get_objects(self):
        return self.register

    def get_serializer(self, **kwargs):
        return self.serializer_class(
            many=True,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        operation_id="validation_plugin_list",
        summary=_("List available validation plugins"),
    )
    def get(self, request, *args, **kwargs):
        objects = self.get_objects()
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)


class ValidationView(APIView):
    """
    Validate a value using given validator
    """

    register = register
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

        result = self.register.validate(
            self.kwargs["validator"], serializer.data["value"]
        )
        return Response(ValidationResultSerializer(result).data)
