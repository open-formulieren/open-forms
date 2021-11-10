from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import parsers, permissions, response, status, views, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api.pagination import PageNumberPagination
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin

from ..messages import add_success_message
from ..models import Form, FormDefinition, FormLogic, FormStep, FormVersion
from ..utils import export_form, form_to_json, import_form
from .filters import FormLogicFilter
from .parsers import IgnoreConfigurationFieldCamelCaseJSONParser
from .permissions import IsStaffOrReadOnly
from .serializers import (
    FormAdminMessageSerializer,
    FormDefinitionDetailSerializer,
    FormDefinitionSerializer,
    FormImportSerializer,
    FormLogicSerializer,
    FormSerializer,
    FormStepSerializer,
    FormVersionSerializer,
)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="form_uuid_or_slug",
            location=OpenApiParameter.PATH,
            type=str,
            description=_("Either a UUID4 or a slug identifiying the form."),
        )
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
    queryset = FormStep.objects.all().order_by("order")
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "uuid"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["form"] = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])
        return context


@extend_schema_view(
    list=extend_schema(summary=_("List logic rules")),
    retrieve=extend_schema(summary=_("Retrieve logic rule details")),
    create=extend_schema(summary=_("Create a logic rule")),
    update=extend_schema(summary=_("Update all details of a logic rule")),
    partial_update=extend_schema(summary=_("Update some details of a logic rule")),
    destroy=extend_schema(summary=_("Delete a logic rule")),
)
class FormLogicViewSet(
    viewsets.ModelViewSet,
):
    serializer_class = FormLogicSerializer
    queryset = FormLogic.objects.all()
    permission_classes = [permissions.IsAdminUser]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FormLogicFilter
    lookup_field = "uuid"


@extend_schema_view(
    list=extend_schema(
        summary=_("List form step definitions"),
        tags=["forms", "form-definitions"],
    ),
    retrieve=extend_schema(
        summary=_("Retrieve form step definition details"),
        tags=["forms", "form-definitions"],
    ),
    create=extend_schema(
        summary=_("Create a form definition"),
        tags=["forms", "form-definitions"],
    ),
    update=extend_schema(
        summary=_("Update all details of a form definition"),
        tags=["forms", "form-definitions"],
    ),
    partial_update=extend_schema(
        summary=_("Update some details of a form definition"),
        tags=["forms", "form-definitions"],
    ),
    destroy=extend_schema(
        summary=_("Delete a form definition"),
        tags=["forms", "form-definitions"],
    ),
)
class FormDefinitionViewSet(viewsets.ModelViewSet):
    parser_classes = (IgnoreConfigurationFieldCamelCaseJSONParser,)
    queryset = FormDefinition.objects.order_by("slug")
    serializer_class = FormDefinitionSerializer
    pagination_class = PageNumberPagination
    lookup_field = "uuid"
    # anonymous clients must be able to get the form definitions in the browser
    # The DRF settings apply some default throttling to mitigate abuse
    permission_classes = [IsStaffOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FormDefinitionDetailSerializer
        return super().get_serializer_class()

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


UUID_OR_SLUG_PARAMETER = OpenApiParameter(
    name="uuid_or_slug",
    location=OpenApiParameter.PATH,
    type=str,
    description=_("Either a UUID4 or a slug identifiying the form."),
)


@extend_schema_view(
    list=extend_schema(
        summary=_("List forms"),
        description=_(
            "List the active forms, including the pointers to the form steps. "
            "Form steps are included in order as they should appear."
        ),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve form details"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    create=extend_schema(summary=_("Create form")),
    update=extend_schema(
        summary=_("Update all details of a form"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    partial_update=extend_schema(
        summary=_("Update given details of a form"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    destroy=extend_schema(
        summary=_("Mark form as deleted"),
        description=_(
            "Destroying a form leads to a soft-delete to protect related submissions. "
            "These deleted forms are no longer visible in the API endpoints."
        ),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
)
class FormViewSet(viewsets.ModelViewSet):
    """
    Manage forms.

    Forms are collections of form steps, where each form step points to a formio.js
    form definition. Multiple definitions are combined in logical steps to build a
    multi-step/page form for end-users to fill out. Form definitions can be (and are)
    re-used among different forms.
    """

    queryset = Form.objects.all().prefetch_related(
        Prefetch(
            "formstep_set",
            queryset=FormStep.objects.select_related("form_definition").order_by(
                "order"
            ),
        )
    )
    lookup_url_kwarg = "uuid_or_slug"
    # lookup_value_regex = "[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"
    serializer_class = FormSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(active=True, _is_deleted=False)
        return queryset

    def initialize_request(self, request, *args, **kwargs):
        """
        Method overridden to account for the lookup on uuid OR slug.
        """
        request = super().initialize_request(request, *args, **kwargs)

        if not self.kwargs:
            return request

        # mutate self.kwargs based on the type of the lookup_value
        lookup_value = self.kwargs[self.lookup_url_kwarg]
        try:
            UUID(lookup_value)
            self.lookup_field = "uuid"
        except (TypeError, ValueError, AttributeError):  # not a valid UUID
            self.lookup_field = "slug"

        return request

    @extend_schema(
        summary=_("Copy form"),
        tags=["forms"],
        request=None,
        responses={status.HTTP_201_CREATED: FormSerializer},
        parameters=[
            UUID_OR_SLUG_PARAMETER,
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
        copied_form.refresh_from_db()  # this clears any prefetch caches
        serializer = self.get_serializer(instance=copied_form)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        summary=_("Export form"),
        tags=["forms"],
        parameters=[UUID_OR_SLUG_PARAMETER],
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

        export_form(instance.id, response=response)

        response["Content-Length"] = len(response.content)
        return response

    def perform_destroy(self, instance):
        instance._is_deleted = True
        instance.save()

    @extend_schema(
        summary=_("Prepare form edit admin message"),
        tags=["admin"],
        parameters=[UUID_OR_SLUG_PARAMETER],
        request=FormAdminMessageSerializer,
        responses={
            status.HTTP_201_CREATED: FormAdminMessageSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=(permissions.IsAdminUser,),
        url_path="admin-message",
    )
    def admin_message(self, request, *args, **kwargs):
        """
        Prepare the relevant message to be displayed in the admin.

        On form create/update, a success message is displayed to the end user on
        page reload. This exact message varies with the type of submit action that was
        performed and whether the object was created or updated.

        This endpoint is only available for staff users and prepares messages for display
        in the admin environment.
        """
        form = self.get_object()
        serializer = FormAdminMessageSerializer(
            data=request.data,
            context={"request": request, "form": form},
        )
        serializer.is_valid(raise_exception=True)
        add_success_message(
            request,
            form,
            serializer.validated_data["submit_action"],
            serializer.validated_data["is_create"],
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="form_uuid_or_slug",
            location=OpenApiParameter.PATH,
            type=str,
            description=_("Either a UUID4 or a slug identifying the form."),
        )
    ]
)
@extend_schema_view(
    create=extend_schema(
        summary=_("Save form version"),
        tags=["forms"],
    ),
    restore=extend_schema(
        summary=_("Restore form version"),
        tags=["forms"],
        parameters=[
            OpenApiParameter(
                name="form_uuid_or_slug",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("Either a UUID4 or a slug identifying the form."),
            ),
            OpenApiParameter(
                name="uuid",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("The UUID of the form version"),
            ),
        ],
        responses={status.HTTP_204_NO_CONTENT: ""},
    ),
    list=extend_schema(
        summary=_("List form versions"),
        tags=["forms"],
        parameters=[
            OpenApiParameter(
                name="form_uuid_or_slug",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("Either a UUID4 or a slug identifying the form."),
            )
        ],
    ),
)
class FormVersionViewSet(NestedViewSetMixin, ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FormVersionSerializer
    queryset = FormVersion.objects.all()
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "uuid"
    parent_lookup_kwargs = {"form_uuid_or_slug": "form__uuid"}

    def create(self, request, *args, **kwargs):
        """Save the current version of the form so that it can later be retrieved"""

        form = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])

        form_json = form_to_json(form.id)
        form_version = FormVersion.objects.create(form=form, export_blob=form_json)

        serializer = self.serializer_class(instance=form_version)
        return Response(status=status.HTTP_201_CREATED, data=serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        """Restore a previously saved version of a form."""
        form = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])
        form_version = get_object_or_404(FormVersion, uuid=self.kwargs["uuid"])

        form.restore_old_version(form_version.uuid)

        return Response(status=status.HTTP_201_CREATED)


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

        import_form(serializer.validated_data["file"])

        return response.Response(status=status.HTTP_204_NO_CONTENT)
