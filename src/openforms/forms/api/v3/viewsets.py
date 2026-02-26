from typing import TypedDict, Unpack
from uuid import UUID

from django.http import Http404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from ...api.parsers import FormCamelCaseJSONParser
from ...api.permissions import FormAPIPermissions
from ...api.renderers import FormCamelCaseJSONRenderer
from ...models.form import Form
from .serializers import FormSerializer


class KwargsType(TypedDict):
    uuid: UUID


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
    permission_classes = (FormAPIPermissions,)

    def update(self, request: Request, **kwargs: Unpack[KwargsType]) -> Response:
        try:
            self.object = self.get_object()
        except Http404:
            self.object = None

        lookup_url_kwarg = self.lookup_url_kwarg or "uuid"
        serializer = self.get_serializer(
            self.object,
            data=request.data,
            context={
                **self.get_serializer_context(),
                "form_uuid": kwargs[lookup_url_kwarg],
            },
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        if self.object is None:
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_200_OK
        return Response(serializer.data, status=status_code)
