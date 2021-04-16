from django.core.management import CommandError, call_command
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import (
    exceptions,
    mixins,
    parsers,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin

from openforms.api.pagination import PageNumberPagination

from ..models import Form, FormDefinition, FormStep
from .permissions import IsStaffOrReadOnly
from .serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)


@extend_schema(
    parameters=[
        OpenApiParameter("form_uuid", OpenApiTypes.UUID, location=OpenApiParameter.PATH)
    ]
)
@extend_schema_view(
    list=extend_schema(summary=_("List form steps")),
    retrieve=extend_schema(summary=_("Retrieve form step details")),
    create=extend_schema(summary=_("Create a form step")),
    update=extend_schema(summary=_("Update all details of a form step")),
    partial_update=extend_schema(summary=_("Update some details of a form step")),
    destroy=extend_schema(summary=_("Delete a form step")),
)
class FormStepViewSet(
    NestedViewSetMixin,
    viewsets.ModelViewSet,
):
    serializer_class = FormStepSerializer
    queryset = FormStep.objects.all()
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "uuid"


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
class FormDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormDefinition.objects.order_by("slug")
    serializer_class = FormDefinitionSerializer
    pagination_class = PageNumberPagination
    lookup_field = "uuid"
    # anonymous clients must be able to get the form definitions in the browser
    # The DRF settings apply some default throttling to mitigate abuse
    permission_classes = [permissions.AllowAny]

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
    create=extend_schema(summary=_("Create form")),
    update=extend_schema(summary=_("Update all details of a form")),
    partial_update=extend_schema(summary=_("Update given details of a form")),
)
class FormViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Form.objects.filter(active=True)
    lookup_field = "uuid"
    serializer_class = FormSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_authenticators(self):
        if self.name == "Export":
            return [TokenAuthentication()]
        return super().get_authenticators()

    @action(detail=True, methods=["post"])
    def export(self, request, *args, **kwargs):
        """
        Exports the Form and related FormDefinitions and FormSteps as a .zip
        """
        instance = self.get_object()

        response = HttpResponse(content_type="application/zip")
        filename = instance.slug
        response["Content-Disposition"] = "attachment;filename={}".format(
            f"{filename}.zip"
        )

        call_command("export", response=response, form_id=instance.id)

        response["Content-Length"] = len(response.content)
        return response


class FormsImportAPIView(views.APIView):
    parser_classes = (parsers.FileUploadParser,)
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsStaffOrReadOnly]

    def post(self, request, *args, **kwargs):
        """
        Import a form

        Import forms by uploading a .zip file
        """

        try:
            call_command("import", import_file_content=request.FILES["file"].read())
        except CommandError as e:
            raise exceptions.ValidationError({"error": e})

        return response.Response(status=status.HTTP_204_NO_CONTENT)
