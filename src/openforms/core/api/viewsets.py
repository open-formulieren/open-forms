from rest_framework import permissions, viewsets
from rest_framework_nested.viewsets import NestedViewSetMixin

from ..api.serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)
from ..models import Form, FormDefinition, FormStep


class BaseFormsViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    # anonymous clients must be able to get the form definitions in the browser
    # The DRF settings apply some default throttling to prevent abuse
    permission_classes = [permissions.AllowAny]


class FormStepViewSet(NestedViewSetMixin, BaseFormsViewSet):
    serializer_class = FormStepSerializer
    queryset = FormStep.objects.all()


class FormDefinitionViewSet(BaseFormsViewSet):
    queryset = FormDefinition.objects.filter()
    serializer_class = FormDefinitionSerializer

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        return {**context, "handle_custom_types": False}


class FormViewSet(BaseFormsViewSet):
    queryset = Form.objects.filter(active=True)
    serializer_class = FormSerializer
