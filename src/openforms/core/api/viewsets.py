from rest_framework import permissions, viewsets

from openforms.core.api.serializers import (
    FormSerializer, FormDefinitionSerializer, FormStepSerializer
)
from openforms.core.models import Form, FormDefinition


class FormStepViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    serializer_class = FormStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FormDefinition.objects.filter(slug=self.kwargs['slug'])


class FormDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    queryset = FormDefinition.objects.filter()
    serializer_class = FormDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    queryset = Form.objects.filter(active=True)
    serializer_class = FormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
