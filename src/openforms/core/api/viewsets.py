import json

from django.http import JsonResponse, Http404
from rest_framework import permissions, views, viewsets
from rest_framework.generics import get_object_or_404

from openforms.core.api.serializers import FormSerializer
from openforms.core.models import FormDefinition


class ConfigurationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        form = get_object_or_404(FormDefinition, slug=kwargs['slug'])
        if form.active:
            return JsonResponse(json.loads(form.configuration))
        else:
            raise Http404


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    queryset = FormDefinition.objects.filter(active=True)
    serializer_class = FormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
