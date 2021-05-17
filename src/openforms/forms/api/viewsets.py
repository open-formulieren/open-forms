from django.core.management import CommandError, call_command
from django.db import transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

import reversion
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
from rest_framework.settings import api_settings
from reversion.views import RevisionMixin

from openforms.api.pagination import PageNumberPagination
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin

from ..models import Form, FormDefinition, FormStep
from .permissions import IsStaffOrReadOnly
from .serializers import (
    FormDefinitionSerializer,
    FormImportSerializer,
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
    permission_classes = [permissions.AllowAny]
    lookup_field = "uuid"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["form"] = get_object_or_404(Form, uuid=self.kwargs["form_uuid"])
        return context


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
    list=extend_schema(
        summary=_("List forms"),
        description=_(
            "List the active forms, including the pointers to the form steps. "
            "Form steps are included in order as they should appear."
        ),
    ),
    retrieve=extend_schema(summary=_("Retrieve form details")),
    create=extend_schema(summary=_("Create form")),
    update=extend_schema(summary=_("Update all details of a form")),
    partial_update=extend_schema(summary=_("Update given details of a form")),
    destroy=extend_schema(
        summary=_("(Soft) delete a form"),
        description=_(
            "Destroying a form leads to a soft-delete to protect related submissions. "
            "These deleted forms are no longer visible in the API endpoints."
        ),
    ),
)
class FormViewSet(RevisionMixin, viewsets.ModelViewSet):
    """
    Manage forms.

    Forms are collections of form steps, where each form step points to a formio.js
    form definition. Multiple definitions are combined in logical steps to build a
    multi-step/page form for end-users to fill out. Form definitions can be (and are)
    re-used among different forms.
    """

    queryset = Form.objects.filter(active=True, _is_deleted=False)
    lookup_field = "uuid"
    serializer_class = FormSerializer
    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        summary=_("Copy form"),
        tags=["forms"],
        request=None,
        responses={status.HTTP_201_CREATED: FormSerializer},
        parameters=[
            OpenApiParameter(
                name="Location",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.HEADER,
                description="URL of the created resource",
                response=[status.HTTP_201_CREATED],
            ),
        ],
    )
    @transaction.atomic
    @action(
        detail=True, methods=["post"], authentication_classes=(TokenAuthentication,)
    )
    def copy(self, request, *args, **kwargs):
        """
        Create a copy of a form.

        Copying a form copies the meta-data of the form and the steps included.
        Referenced form definitions inside the form steps are re-used instead of
        new copies being created.
        """
        instance = self.get_object()
        copied_form = instance.copy()
        serializer = self.get_serializer(instance=copied_form)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        summary=_("Export form"),
        tags=["forms"],
        request=None,
        responses={
            (
                status.HTTP_200_OK,
                "application/zip",
            ): OpenApiTypes.BINARY
        },
    )
    @action(
        detail=True, methods=["post"], authentication_classes=(TokenAuthentication,)
    )
    def export(self, request, *args, **kwargs):
        """
        Export a form with the related steps and form definitions as a ZIP-file.

        The exported ZIP-file can be used to import complete forms.
        """
        instance = self.get_object()

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = f"attachment;filename={instance.slug}.zip"

        call_command("export", instance.id, response=response)

        response["Content-Length"] = len(response.content)
        return response

    def perform_destroy(self, instance):
        instance._is_deleted = True
        instance.save()
        reversion.set_comment(_("Formulier verwijderd via API."))


class FormsImportAPIView(views.APIView):
    serializer_class = FormImportSerializer
    parser_classes = (parsers.FileUploadParser,)
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary=_("Import form"),
        tags=["forms"],
        responses={"204": {"description": _("No response body")}},
    )
    def post(self, request, *args, **kwargs):
        """
        Import a Form by uploading a .zip file containing a Form, FormDefinitions
        and FormSteps
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            call_command("import", import_file=serializer.validated_data["file"])
        except CommandError as e:
            raise exceptions.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: e})

        return response.Response(status=status.HTTP_204_NO_CONTENT)
