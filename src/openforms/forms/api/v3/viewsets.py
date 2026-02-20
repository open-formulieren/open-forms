from django.http import Http404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.forms.api.parsers import FormCamelCaseJSONParser
from openforms.forms.api.permissions import FormAPIPermissions
from openforms.forms.api.renderers import FormCamelCaseJSONRenderer
from openforms.forms.api.v3.serializers import FormSerializer
from openforms.forms.models.form import Form


# Uses "PUT as create", see https://www.django-rest-framework.org/api-guide/generic-views/#put-as-create
# and diff from rest framework version 3.0 and earlier (b106ebd2c0a19107f12d5b87cfbe0083aaaa60b9)
@extend_schema_view(
    update=extend_schema(
        summary=_("Create or update all details of a form"),
        tags=["forms"],
    ),
)
class FormViewSet(viewsets.GenericViewSet):
    parser_classes = (FormCamelCaseJSONParser,)
    renderer_classes = (FormCamelCaseJSONRenderer,)
    queryset = Form.objects.all()
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    serializer_class = FormSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (FormAPIPermissions,)

    def update(self, request: Request, **kwargs) -> Response:
        try:
            self.object = self.get_object()
        except Http404:
            self.object = None

        serializer = self.get_serializer(
            self.object,
            data=request.data,
            context={
                **self.get_serializer_context(),
                "uuid": kwargs.get(self.lookup_url_kwarg),  # pyright: ignore[reportArgumentType]
            },
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if self.object is None:
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_200_OK

        serializer.save()
        return Response(serializer.data, status=status_code)
