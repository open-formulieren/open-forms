from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.drf_spectacular.plumbing import extend_inline_serializer
from openforms.api.views import ListMixin
from openforms.submissions.api.permissions import owns_submission
from openforms.submissions.models import Submission
from openforms.submissions.parsers import IgnoreValueFieldCamelCaseJSONParser
from openforms.validations.api.serializers import (
    ValidationInputSerializer,
    ValidationPluginSerializer,
    ValidationResultSerializer,
    ValidatorsFilterSerializer,
)

from ..base import BasePlugin
from ..registry import register


@extend_schema_view(
    get=extend_schema(
        summary=_("List available validation plugins"),
        parameters=[*ValidatorsFilterSerializer.as_openapi_params()],
    ),
)
class ValidatorsListView(ListMixin, APIView):
    """
    List available validation plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ValidationPluginSerializer

    def get_objects(self) -> list[BasePlugin]:
        filter_serializer = ValidatorsFilterSerializer(data=self.request.query_params)
        if not filter_serializer.is_valid(raise_exception=False):
            return []

        plugins = register.iter_enabled_plugins()
        for_component: str = (
            filter_serializer.validated_data.get("component_type") or ""
        )

        if not for_component:
            return list(plugins)
        return [plugin for plugin in plugins if for_component in plugin.for_components]


class ValidationView(APIView):
    """
    Validate a value using given validator
    """

    authentication_classes = (AnonCSRFSessionAuthentication,)
    parser_classes = [IgnoreValueFieldCamelCaseJSONParser]

    @extend_schema(
        operation_id="validation_run",
        summary=_("Validate value using validation plugin"),
        request=extend_inline_serializer(
            ValidationInputSerializer,
            {
                "value": serializers.JSONField(
                    label=_("value"), help_text=_("Value to be validated.")
                )
            },
        ),
        responses=ValidationResultSerializer,
        parameters=[
            OpenApiParameter(
                "validator",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                enum=sorted([validator.identifier for validator in register]),
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

        if not owns_submission(request, serializer.data["submission_uuid"]):
            raise PermissionDenied()

        submission = Submission.objects.get(uuid=serializer.data["submission_uuid"])
        result = register.validate(
            self.kwargs["validator"], request.data["value"], submission
        )
        return Response(ValidationResultSerializer(result).data)
