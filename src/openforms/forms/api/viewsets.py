from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin

from openforms.api.pagination import PageNumberPagination

from ..api.permissions import IsStaffOrReadOnly
from ..api.serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)
from ..models import Form, FormDefinition, FormStep


class BaseFormsViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    # anonymous clients must be able to get the form definitions in the browser
    # The DRF settings apply some default throttling to mitigate abuse
    permission_classes = [permissions.AllowAny]


@extend_schema(
    parameters=[
        OpenApiParameter("form_uuid", OpenApiTypes.UUID, location=OpenApiParameter.PATH)
    ]
)
@extend_schema_view(
    list=extend_schema(summary=_("List form steps")),
    retrieve=extend_schema(summary=_("Retrieve form step details")),
)
class FormStepViewSet(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    BaseFormsViewSet,
):
    serializer_class = FormStepSerializer
    queryset = FormStep.objects.all()
    permission_classes = [IsStaffOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        summary=_("List form step definitions"),
        tags=["forms"],
    ),
    retrieve=extend_schema(
        summary=_("Retrieve form step definition"),
        tags=["forms"],
    ),
)
class FormDefinitionViewSet(BaseFormsViewSet):
    queryset = FormDefinition.objects.order_by("slug")
    serializer_class = FormDefinitionSerializer
    pagination_class = PageNumberPagination

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        return {**context, "handle_custom_types": False}

    @extend_schema(
        summary=_("Retrieve form definition JSON schema"),
        tags=["forms"],
        responses=OpenApiTypes.OBJECT,
    )
    @action(methods=("GET",), detail=True)
    def configuration(self, request: Request, *args, **kwargs):
        """
        Return the raw FormIO.js configuration definition.

        This excludes all the meta-data and just returns the JSON schema blob. In
        theory, this can be fed directly to a FormIO.js renderer, but note that there
        may be custom field types in play.
        """
        definition = self.get_object()
        return Response(data=definition.configuration, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary=_("List forms")),
    retrieve=extend_schema(summary=_("Retrieve form details")),
)
class FormViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, BaseFormsViewSet):
    queryset = Form.objects.filter(active=True)
    serializer_class = FormSerializer
    permission_classes = [IsStaffOrReadOnly]
