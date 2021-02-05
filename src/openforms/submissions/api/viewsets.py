import logging

from django.db import transaction
from django.utils import timezone

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin

from openforms.api import pagination
from openforms.api.filters import PermissionFilterMixin
from openforms.core.backends import registry

from ..models import Submission, SubmissionStep
from ..utils import add_submmission_to_session, remove_submission_from_session
from .permissions import ActiveSubmissionPermission
from .serializers import (
    SubmissionSerializer,
    SubmissionStepSerializer,
    SubmissionSuspensionSerializer,
)
from .validation import CompletionValidationSerializer, validate_submission_completion

logger = logging.getLogger(__name__)


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
            self.instance.bsn = bsn
            self.instance.save(update_fields=["bsn"])

        # store the submission ID in the session, so that only the session owner can
        # mutate/view the submission
        # note: possible race condition with concurrent requests
        add_submmission_to_session(serializer.instance, self.request)

    # @swagger_auto_schema(
    #     request_body=no_body,
    #     responses={
    #         204: "",
    #         400: CompletionValidationSerializer,
    #     },
    # )
    @transaction.atomic()
    @action(detail=True, methods=["post"], url_name="complete")
    def _complete(self, request, *args, **kwargs):
        """
        Mark the submission as completed.

        Submission completion requires that all required steps are completed.

        Once a submission is completed, it's removed from the session. This means it's
        no longer possible to change or read the submission data (including individual
        steps).

        The submissions is persisted to the configured backend.
        """
        submission = self.get_object()
        validate_submission_completion(submission, request=request)
        submission.completed_on = timezone.now()
        backend_func = registry.get(submission.form.backend)
        if backend_func:
            result = backend_func(submission)
            submission.backend_result = result
        submission.save()
        remove_submission_from_session(submission, self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @swagger_auto_schema(
    #     request_body=SubmissionSuspensionSerializer,
    #     responses={
    #         201: SubmissionSuspensionSerializer,
    #         # 400: TODO - schema for errors!
    #     },
    # )
    @transaction.atomic()
    @action(detail=True, methods=["post"], url_name="suspend")
    def _suspend(self, request, *args, **kwargs):
        """
        Suspend the submission.

        Submission suspension requires contact details to send the end-user the resume
        URL so that they can resume the submission (possible from another device).
        """
        submission = self.get_object()
        serializer = SubmissionSuspensionSerializer(
            instance=submission, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubmissionStepViewSet(
    NestedViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Handle form step submission data.

    retrieve:
    Retrieve the form step submission details.

    update:
    Submit the form step submission data.

    The submission data is either created or updated, depending on whether there was
    submission data present before or not. Make sure to retrieve the step data to
    display already filled out fields.

    Note that the form step configuration is currently not validated - this may change
    in the future. I.e. - a step that is marked as not available will still be submitted
    at the time being.
    """

    queryset = SubmissionStep.objects.all()
    serializer_class = SubmissionStepSerializer
    authentication_classes = ()
    permission_classes = [ActiveSubmissionPermission]
    lookup_url_kwarg = "step_uuid"
    submission_url_kwarg = "submission_uuid"

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

    def update(self, request, *args, **kwargs):
        """
        Update or create a form submission step.

        Partial updates are not allowed - PUT is used for both creating or updating
        the submission step data.
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
