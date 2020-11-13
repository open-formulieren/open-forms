from rest_framework import permissions, viewsets

from ..api.serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)
from ..models import Form, FormDefinition, FormStep


class FormStepViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'uuid'
    serializer_class = FormStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FormStep.objects.filter(form__uuid=self.kwargs['form_uuid'])


class FormDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'uuid'
    queryset = FormDefinition.objects.filter()
    serializer_class = FormDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'uuid'
    queryset = Form.objects.filter(active=True)
    serializer_class = FormSerializer
    # anonymous clients must be able to get the form definitions in the browser
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
