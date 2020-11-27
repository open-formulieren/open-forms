import logging

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin

from openforms.core.backends import registry
from openforms.core.models import Form

from ..models import Submission, SubmissionStep
from ..utils import add_submmission_to_session
from .permissions import ActiveSubmissionPermission
from .serializers import SubmissionSerializer, SubmissionStepSerializer

logger = logging.getLogger(__name__)


class FormSubmissionViewSet(viewsets.ViewSet):
    lookup_field = "uuid"
    # TODO: Handle auth correctly / remove this Auth
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = None

    def create_new_submission(self, request):
        data = {"form": self.form}
        # TODO: Check if the user has existing incomplete submission under their BSN.
        bsn = request.session.get("bsn")
        if bsn:
            data["bsn"] = bsn
        submission = Submission.objects.create(**data)
        request.session[self.form.uuid] = str(submission.uuid)
        return submission

    @staticmethod
    def validate_data(request, last_step):
        errors = []

        data = request.data.get("data")
        step_index = request.data.get("step_index")
        next_step_index = request.data.get("next_step_index")
        if not data:
            errors.append("No data supplied")

        if step_index:
            if step_index > last_step:
                errors.append("`step_index` not an existing form step.")
        if next_step_index:
            if next_step_index > last_step:
                errors.append("`next_step_index` not an existing form step.")

        return {
            "data": data,
            "step_index": step_index,
            "next_step_index": next_step_index,
        }, errors

    @action(detail=True, methods=["post"])
    def submit(self, request, uuid=None):
        self.form = get_object_or_404(Form, uuid=uuid)
        # TODO: Rate limit/throttle this, since someone can just keep hitting this
        # with different sessions and fill up the DB.
        submission_uuid = request.session.get(self.form.uuid)
        if not submission_uuid:
            submission = self.create_new_submission(request)
        else:
            try:
                submission = Submission.objects.get(uuid=submission_uuid)
            except Submission.DoesNotExist:
                logger.info("Session Submission does not exist. Recreating...")
                submission = self.create_new_submission(request)

        last_step = submission.form.formstep_set.aggregate(Max("order"))["order__max"]

        if submission.completed_on:
            return Response(
                data={"reason": "Submission completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: Validate data that is posted and saved at the current step.
        data, errors = self.validate_data(request, last_step)
        if not errors:
            current_step = data["step_index"] or submission.current_step
            submission_step = SubmissionStep.objects.create(
                submission=submission,
                form_step=submission.form.formstep_set.get(order=current_step),
                data=data["data"],
            )
            if data["next_step_index"]:
                submission.current_step = data["next_step_index"]
            else:
                submission.current_step = current_step + 1
            if submission.current_step > last_step:
                submission.completed_on = timezone.now()
                backend_func = registry.get(submission.form.backend)
                if backend_func:
                    result = backend_func(submission_step)
                    submission.backend_result = result
            submission.save()

            serializer = SubmissionSerializer(
                instance=submission, context={"request": request}
            )

            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data={"reason": errors}, status=status.HTTP_400_BAD_REQUEST)


class SubmissionViewSet(
    mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    authentication_classes = ()
    permission_classes = [ActiveSubmissionPermission]
    lookup_field = "uuid"

    @transaction.atomic
    def perform_create(self, serializer):
        super().perform_create(serializer)

        # store the submission ID in the session, so that only the session owner can
        # mutate/view the submission
        # note: possible race condition with concurrent requests
        add_submmission_to_session(serializer.instance, self.request)


class SubmissionStepViewSet(
    NestedViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
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
