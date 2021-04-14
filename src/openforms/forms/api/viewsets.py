from django.core.management import CommandError, call_command
from django.db import transaction
from django.db.utils import DataError, IntegrityError
from django.http.response import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import (
    exceptions,
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

from ..api.permissions import IsStaffOrReadOnly
from ..api.serializers import (
    FormDefinitionSerializer,
    FormSerializer,
    FormStepSerializer,
)
from ..models import Form, FormDefinition, FormStep
from ..utils import copy_form


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
class FormStepViewSet(NestedViewSetMixin, BaseFormsViewSet):
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
class FormViewSet(BaseFormsViewSet):
    queryset = Form.objects.filter(active=True)
    serializer_class = FormSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_authenticators(self):
        if self.name in ["Export", "Copy"]:
            return [TokenAuthentication()]
        return super().get_authenticators()

    @transaction.atomic
    @action(detail=True, methods=["post"])
    def copy(self, request, *args, **kwargs):
        """
        Copies a Form and all related FormSteps/FormDefinitions
        """
        instance = self.get_object()

        try:
            copied_form = copy_form(instance)
        except (DataError, IntegrityError) as e:
            return Response({"error": f"Error occurred while copying: {e}"}, status=400)

        path = reverse("api:form-detail", kwargs={"uuid": copied_form.uuid})
        detail_url = request.build_absolute_uri(path)

        return Response(status=201, headers={"Location": detail_url})

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
