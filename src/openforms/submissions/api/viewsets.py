import logging

from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from openforms.api import pagination
from openforms.api.filters import PermissionFilterMixin
from openforms.registrations.tasks import (
    cleanup_temporary_files_for,
    generate_submission_report,
    register_submission,
)
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin

from ...appointments.utils import book_appointment_for_submission
from ..attachments import attach_uploads_to_submission_step
from ..form_logic import evaluate_form_logic
from ..models import Submission, SubmissionReport, SubmissionStep
from ..parsers import IgnoreDataFieldCamelCaseJSONParser
from ..tokens import token_generator
from ..utils import (
    add_submmission_to_session,
    remove_submission_from_session,
    remove_submission_uploads_from_session,
    send_confirmation_email,
)
from .permissions import ActiveSubmissionPermission
from .serializers import (
    FormDataSerializer,
    SubmissionCompletionSerializer,
    SubmissionSerializer,
    SubmissionStepSerializer,
    SubmissionSuspensionSerializer,
)
from .validation import CompletionValidationSerializer, validate_submission_completion

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary=_("List active submissions"),
        description=_(
            "Active submissions are submissions whose ID is in the user session. "
            "This endpoint returns user-bound submissions. Note that you get different "
            "results on different results because of the differing sessions."
        ),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve submission details"),
        description=_("Get the state of a single submission in the user session."),
    ),
    create=extend_schema(
        summary=_("Start a submission"),
        description=_(
            "Start a submission for a particular form. The submission is added to the "
            "user session."
        ),
    ),
)
class SubmissionViewSet(
    PermissionFilterMixin, mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Submission.objects.order_by("created_on")
    serializer_class = SubmissionSerializer
    authentication_classes = ()
    permission_classes = [ActiveSubmissionPermission]
    lookup_field = "uuid"
    pagination_class = pagination.PageNumberPagination

    @transaction.atomic
    def perform_create(self, serializer):
        super().perform_create(serializer)

        bsn = self.request.session.get("bsn")
        if bsn:
            instance = serializer.instance
            instance.bsn = bsn
            instance.save(update_fields=["bsn"])

        # store the submission ID in the session, so that only the session owner can
        # mutate/view the submission
        # note: possible race condition with concurrent requests
        add_submmission_to_session(serializer.instance, self.request.session)

    @extend_schema(
        summary=_("Complete a submission"),
        request=None,
        responses={
            200: SubmissionCompletionSerializer,
            400: CompletionValidationSerializer,
        },
    )
    @transaction.atomic()
    @action(detail=True, methods=["post"], url_name="complete")
    def _complete(self, request, *args, **kwargs):
        """
        Mark the submission as completed.

        Submission completion requires that all required steps are completed.

        Once a submission is completed, it's removed from the session. This means it's
        no longer possible to change or read the submission data (including individual
        steps).

        The submission is persisted to the configured backend.
        """
        submission = self.get_object()
        validate_submission_completion(submission, request=request)
        submission.completed_on = timezone.now()

        submission.save()
        remove_submission_from_session(submission, self.request.session)
        remove_submission_uploads_from_session(submission, self.request.session)

        submission_report = SubmissionReport.objects.create(
            title=_("%(title)s: Submission report") % {"title": submission.form.name},
            submission=submission,
        )

        def on_submission_commit():
            # The submission report needs to already have been generated before it can be attached to the zaak
            # that is created in the registration
            chain = generate_submission_report.si(
                submission_report.id
            ) | register_submission.si(submission.id)
            chain.delay()

            # this can run any time because they have been claimed earlier
            cleanup_temporary_files_for.delay(submission.id)

        transaction.on_commit(on_submission_commit)

        book_appointment_for_submission(submission)

        if hasattr(submission.form, "confirmation_email_template"):
            transaction.on_commit(lambda: send_confirmation_email(submission))

        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )
        report_status_url = reverse(
            "api:submissions:submission-report-status",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        serializer = SubmissionCompletionSerializer(
            instance={
                "download_url": request.build_absolute_uri(download_report_url),
                "report_status_url": request.build_absolute_uri(report_status_url),
                "confirmation_page_content": submission.render_confirmation_page(),
            },
        )
        return Response(serializer.data)

    @extend_schema(
        summary=_("Suspend a submission"),
        request=SubmissionSuspensionSerializer,
        responses={
            201: SubmissionSuspensionSerializer,
            # 400: TODO - schema for errors
        },
    )
    @transaction.atomic()
    @action(detail=True, methods=["post"], url_name="suspend")
    def _suspend(self, request, *args, **kwargs):
        """
        Suspend the submission.

        Submission suspension requires contact details to send the end-user a URL to
        resume the submission (possibly from another device).
        """
        submission = self.get_object()
        serializer = SubmissionSuspensionSerializer(
            instance=submission, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "submission_uuid", OpenApiTypes.UUID, location=OpenApiParameter.PATH
        ),
        OpenApiParameter(
            "step_uuid", OpenApiTypes.UUID, location=OpenApiParameter.PATH
        ),
    ]
)
@extend_schema_view(
    retrieve=extend_schema(
        summary=_("Retrieve step details"),
        description=_(
            "The details of a particular submission step always return the related "
            "form step configuration. If there is no data yet for the step, the ID "
            "will be `null`. Set the step data by making a `PUT` request."
        ),
    )
)
class SubmissionStepViewSet(
    NestedViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Handle form step submission data.
    """

    queryset = SubmissionStep.objects.all()
    serializer_class = SubmissionStepSerializer
    authentication_classes = ()
    permission_classes = [ActiveSubmissionPermission]
    lookup_url_kwarg = "step_uuid"
    submission_url_kwarg = "submission_uuid"
    parser_classes = [IgnoreDataFieldCamelCaseJSONParser]

    def get_object(self):
        """
        Retrieve a SubmissionStep instance in the context of the current submission.

        This is a custom implementation, because the :class:`SubmissionStep` record may
        not exist yet for GET calls because no data has been submitted yet. In that case,
        a new, unsaved instance is used for the serializer.

        The URL path kwargs resolve the static form step definition, apply the
        submission context and possibly transform the form definition.
        """
        submission_uuid = self.kwargs["submission_uuid"]
        qs = SubmissionStep.objects.filter(
            submission__uuid=submission_uuid,
            form_step__uuid=self.kwargs["step_uuid"],
        )
        try:
            submission_step = qs.get()
        except SubmissionStep.DoesNotExist:
            submission = get_object_or_404(
                Submission.objects.select_related("form"), uuid=submission_uuid
            )
            form_step = get_object_or_404(
                submission.form.formstep_set, uuid=self.kwargs["step_uuid"]
            )
            submission_step = SubmissionStep(
                uuid=None,
                submission=submission,
                form_step=form_step,
            )
        self.check_object_permissions(self.request, submission_step)
        return submission_step

    @extend_schema(summary=_("Store submission step data"))
    def update(self, request, *args, **kwargs):
        """
        The submission data is either created or updated, depending on whether there was
        submission data present before or not. Make sure to retrieve the step data to
        display already filled out fields.

        Note that the form step configuration is currently not validated - this may change
        in the future. I.e. - a step that is marked as not available will still be submitted
        at the time being.
        """
        instance = self.get_object()
        create = instance.pk is None
        if create:
            instance.uuid = SubmissionStep._meta.get_field("uuid").default()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        attach_uploads_to_submission_step(instance)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        status_code = status.HTTP_200_OK if not create else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)

    @extend_schema(
        description=_("Apply/check form logic"),
        request=FormDataSerializer,
    )
    @action(detail=True, methods=["post"], url_path="_check_logic")
    def logic_check(self, request, *args, **kwargs):
        submission_step = self.get_object()

        form_data_serializer = FormDataSerializer(data=request.data)
        form_data_serializer.is_valid(raise_exception=True)

        data = form_data_serializer.validated_data["data"]
        if data:
            # TODO: probably we should use a recursive merge here, in the event that
            # keys like ``foo.bar`` and ``foo.baz`` are used which construct a foo object
            # with keys bar and baz.
            merged_data = {**submission_step.submission.data, **data}
            evaluate_form_logic(submission_step, merged_data)

        serializer = self.get_serializer(instance=submission_step)
        return Response(serializer.data)
