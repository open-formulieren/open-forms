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
from openforms.registrations.tasks import register_submission
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin

from ..models import Submission, SubmissionStep
from ..parsers import IgnoreDataFieldCamelCaseJSONParser
from ..tokens import token_generator
from ..utils import (
    add_submmission_to_session,
    create_submission_report,
    remove_submission_from_session,
    send_confirmation_email,
)
from .permissions import ActiveSubmissionPermission
from .serializers import (
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
        add_submmission_to_session(serializer.instance, self.request)

    @extend_schema(
        summary=_("Complete a submission"),
        request=None,
        responses={
            204: None,
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

        transaction.on_commit(lambda: register_submission.delay(submission.id))

        if hasattr(submission.form, "confirmation_email_template"):
            transaction.on_commit(lambda: send_confirmation_email(submission))

        submission.save()
        remove_submission_from_session(submission, self.request)

        submission_report = create_submission_report(submission)
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        return Response(
            status=status.HTTP_200_OK, data={"download_url": download_report_url}
        )

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

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        status_code = status.HTTP_200_OK if not create else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)
