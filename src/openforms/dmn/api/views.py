from typing import List

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.utils.api.views import ListMixin

from ..base import DecisionDefinition
from ..registry import register
from .serializers import (
    DecisionDefinitionPlugin,
    DecisionDefinitionVersionPlugin,
    DecisionPluginSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision plugins"),
    ),
)
class PluginListView(ListMixin, APIView):
    """
    List all decision plugins that have been registered.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DecisionPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


ENGINE_PARAMETER = OpenApiParameter(
    name="engine",
    type=str,
    location=OpenApiParameter.QUERY,
    required=True,
    description=_(
        "Identifier of the decision engine to query. Note that some engines "
        "may be disabled at runtime."
    ),
    enum=[engine.identifier for engine in register.iter_enabled_plugins()],
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision definitions"),
        parameters=[ENGINE_PARAMETER],
        responses={
            200: DecisionDefinitionPlugin(many=True),
            400: ValidationErrorSerializer,
            404: ExceptionSerializer,
        },
    ),
)
class DecisionDefinitionListView(ListMixin, APIView):
    """
    List the available decision definitions for a given plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DecisionDefinitionPlugin

    def get_objects(self) -> List[DecisionDefinition]:
        param = ENGINE_PARAMETER.name
        engine = self.request.GET.get(param)
        if not engine:
            raise serializers.ValidationError(
                {param: _(f"The '{param}' query parameter is required.")}
            )
        try:
            plugin = register[engine]
        except KeyError:
            raise NotFound(detail=_("No engine '{engine}' found").format(engine=engine))

        definitions = plugin.get_available_decision_definitions()
        return definitions


DEFINITION_PARAMETER = OpenApiParameter(
    name="definition",
    type=str,
    location=OpenApiParameter.QUERY,
    required=True,
    description=_("Identifier of the definition to retrieve available versions for."),
)


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision definition versions"),
        parameters=[ENGINE_PARAMETER, DEFINITION_PARAMETER],
        responses={
            200: DecisionDefinitionPlugin(many=True),
            400: ValidationErrorSerializer,
            404: ExceptionSerializer,
        },
    ),
)
class DecisionDefinitionVersionListView(ListMixin, APIView):
    """
    List the available versions of a given definition.

    If the selected engine supports multiple versions of decision definitions, they can
    be retrieved through this endpoint. You must specify the engine and selected
    definition ID.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DecisionDefinitionVersionPlugin

    def get_objects(self) -> List[DecisionDefinition]:
        param = ENGINE_PARAMETER.name
        engine = self.request.GET.get(param)
        if not engine:
            raise serializers.ValidationError(
                {param: _(f"The '{param}' query parameter is required.")}
            )
        try:
            plugin = register[engine]
        except KeyError:
            raise NotFound(detail=_("No engine '{engine}' found").format(engine=engine))

        definition_param = DEFINITION_PARAMETER.name
        definition_id = self.request.GET.get(definition_param)
        if not definition_id:
            raise serializers.ValidationError(
                {
                    definition_param: _(
                        f"The '{definition_param}' query parameter is required."
                    )
                }
            )

        versions = plugin.get_decision_definition_versions(definition_id)
        return versions
