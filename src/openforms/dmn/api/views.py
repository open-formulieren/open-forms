from typing import List

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.utils.api.views import ListMixin

from ..base import DecisionDefinition
from ..registry import register
from .mixins import ValidateQueryStringParametersMixin
from .serializers import (
    DecisionDefinitionSerializer,
    DecisionDefinitionVersionSerializer,
    DecisionDefinitionXMLSerializer,
    DecisionPluginSerializer,
)

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

DEFINITION_PARAMETER = OpenApiParameter(
    name="definition",
    type=str,
    location=OpenApiParameter.QUERY,
    required=True,
    description=_("Identifier of the definition to retrieve available versions for."),
)

VERSION_PARAMETER = OpenApiParameter(
    name="version",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
)


def get_plugin(engine: str):
    try:
        plugin = register[engine]
    except KeyError:
        raise NotFound(detail=_("No engine '{engine}' found").format(engine=engine))
    return plugin


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


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision definitions"),
        parameters=[ENGINE_PARAMETER],
        responses={
            200: DecisionDefinitionSerializer(many=True),
            400: ValidationErrorSerializer,
            404: ExceptionSerializer,
        },
    ),
)
class DecisionDefinitionListView(
    ValidateQueryStringParametersMixin, ListMixin, APIView
):
    """
    List the available decision definitions for a given plugin.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DecisionDefinitionSerializer
    validate_params = (ENGINE_PARAMETER,)

    def get_objects(self) -> List[DecisionDefinition]:
        engine = self.validate_query_parameters()[ENGINE_PARAMETER]
        plugin = get_plugin(engine)

        definitions = plugin.get_available_decision_definitions()
        return definitions


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision definition versions"),
        parameters=[ENGINE_PARAMETER, DEFINITION_PARAMETER],
        responses={
            200: DecisionDefinitionVersionSerializer(many=True),
            400: ValidationErrorSerializer,
            404: ExceptionSerializer,
        },
    ),
)
class DecisionDefinitionVersionListView(
    ValidateQueryStringParametersMixin, ListMixin, APIView
):
    """
    List the available versions of a given definition.

    If the selected engine supports multiple versions of decision definitions, they can
    be retrieved through this endpoint. You must specify the engine and selected
    definition ID.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DecisionDefinitionVersionSerializer
    validate_params = (ENGINE_PARAMETER, DEFINITION_PARAMETER)

    def get_objects(self) -> List[DecisionDefinition]:
        query_params = self.validate_query_parameters()
        engine = query_params[ENGINE_PARAMETER]
        definition_id = query_params[DEFINITION_PARAMETER]
        plugin = get_plugin(engine)
        versions = plugin.get_decision_definition_versions(definition_id)
        return versions


@extend_schema_view(
    get=extend_schema(
        summary=_("List available decision definition versions"),
        parameters=[
            ENGINE_PARAMETER,
            VERSION_PARAMETER,
        ],
        responses={
            200: DecisionDefinitionXMLSerializer,
            400: ValidationErrorSerializer,
            404: ExceptionSerializer,
        },
    ),
)
class DecisionDefinitionXMLView(ValidateQueryStringParametersMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    validate_params = (ENGINE_PARAMETER, VERSION_PARAMETER)

    def get(self, request, definition: str, **kwargs):
        query_params = self.validate_query_parameters()
        engine = query_params[ENGINE_PARAMETER]
        version = query_params[VERSION_PARAMETER]
        plugin = get_plugin(engine)
        xml = plugin.get_definition_xml(definition, version=version) or ""
        return Response({"xml": xml})
