import contextlib
from uuid import UUID

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api import pagination
from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.filters import PermissionFilterMixin
from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.throttle_classes import PollingRateThrottle
from openforms.authentication.service import is_authenticated_with_an_allowed_plugin
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.forms.models import Form, FormStep
from openforms.logging import logevent
from openforms.prefill.service import prefill_variables
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin

from ..attachments import attach_uploads_to_submission_step
from ..constants import PostSubmissionEvents
from ..exceptions import FormDeactivated, FormMaintenance
from ..form_logic import check_submission_logic, evaluate_form_logic
from ..metrics import start_counter, step_saved_counter, suspension_counter
from ..models import Submission, SubmissionStep
from ..parsers import (
    IgnoreDataAndConfigFieldCamelCaseJSONParser,
    IgnoreDataAndConfigJSONRenderer,
)
from ..signals import submission_cosigned, submission_start
from ..status import SubmissionProcessingStatus
from ..tasks import on_post_submission_event
from ..utils import (
    add_submmission_to_session,
    check_form_status,
    initialise_user_defined_variables,
    remove_submission_from_session,
)
from .mixins import SubmissionCompletionMixin
from .permissions import (
    ActiveSubmissionPermission,
    CanNavigateBetweenSubmissionStepsPermission,
    FormAuthenticationPermission,
    SubmissionStatusPermission,
)
from .serializers import (
    CosignValidationSerializer,
    FormDataSerializer,
    SubmissionCoSignStatusSerializer,
    SubmissionProcessingStatusSerializer,
    SubmissionReportUrlSerializer,
    SubmissionSerializer,
    SubmissionStateLogic,
    SubmissionStateLogicSerializer,
    SubmissionStepSerializer,
    SubmissionStepSummarySerializer,
    SubmissionSuspensionSerializer,
)
from .validation import SubmissionCompletionSerializer

logger = structlog.stdlib.get_logger(__name__)


@contextlib.contextmanager
def cleanup_deactivated_form_session(request: Request, submission: Submission):
    try:
        yield
    except FormDeactivated:
        remove_submission_from_session(submission, request.session)
        if submission.is_authenticated:
            # do this async, as the transaction is rolled back because of the raised
            # exception.
            submission.auth_info.hash_identifying_attributes(delay=True)
        raise


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
        responses={
            201: SubmissionSerializer,
            400: ValidationErrorSerializer,
            403: ExceptionSerializer,
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
        },
    ),
)
class SubmissionViewSet(
    PermissionFilterMixin,
    SubmissionCompletionMixin,
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = Submission.objects.select_related("form", "form__product").order_by(
        "created_on"
    )
    serializer_class = SubmissionSerializer
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [ActiveSubmissionPermission]
    lookup_field = "uuid"
    pagination_class = pagination.PageNumberPagination

    @property
    def throttle_scope(self):
        # called/checked by the DRF scoped throttle class
        if self.action == "_complete":
            return "submit"
        if self.action == "_suspend":
            return "pause"
        return None

    def get_object(self):
        if not hasattr(self, "_get_object_cache"):
            submission = super().get_object()

            with cleanup_deactivated_form_session(self.request, submission):
                check_form_status(self.request, submission.form)

            self._get_object_cache = submission
            # on the fly, calculate the price if it's not set yet (required for overview screen)
            if submission.completed_on is None:
                check_submission_logic(submission)
                submission.calculate_price(save=False)
        return self._get_object_cache

    @transaction.atomic
    def perform_create(self, serializer: SubmissionSerializer):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().perform_create(serializer)
        submission = serializer.instance
        assert isinstance(submission, Submission)

        form: Form = serializer.validated_data["form"]

        check_form_status(self.request, form)
        anonymous: bool = serializer.validated_data["anonymous"]

        # dispatch signal for modules to tap into
        submission_start.send(
            sender=self.__class__,
            instance=serializer.instance,
            request=self.request,
            anonymous=anonymous,
        )

        # store the submission ID in the session, so that only the session owner can
        # mutate/view the submission
        add_submmission_to_session(submission, self.request.session)

        logevent.submission_start(submission)

        prefill_variables(submission)
        initialise_user_defined_variables(submission)

        logged_in = submission.is_authenticated
        start_counter.add(
            1,
            attributes={
                "form.name": form.name,
                "form.uuid": str(form.uuid),
                "auth.logged_in": logged_in,
                "auth.plugin": submission.auth_info.plugin if logged_in else "",
            },
        )

    @extend_schema(
        summary=_("Retrieve co-sign state"),
        request=None,
        responses={
            200: SubmissionCoSignStatusSerializer,
            403: ExceptionSerializer,
            404: ExceptionSerializer,
            405: ExceptionSerializer,
        },
        deprecated=True,
    )
    @action(detail=True, methods=["get"], url_name="co-sign", url_path="co-sign")
    def co_sign(self, request, *args, **kwargs) -> Response:
        """
        Retrieve co-sign state.
        """
        submission = self.get_object()
        serializer = SubmissionCoSignStatusSerializer(
            instance=submission, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary=_("Co-sign submission"),
        responses={
            200: SubmissionReportUrlSerializer,
            400: ExceptionSerializer,
            403: ExceptionSerializer,
            404: ExceptionSerializer,
            405: ExceptionSerializer,
        },
    )
    @transaction.atomic()
    @action(
        detail=True,
        methods=["post"],
        url_name="cosign",
    )
    def cosign(self, request, *args, **kwargs):
        submission = self.get_object()

        if not submission.is_completed:
            raise PermissionDenied(
                _("The submission must be completed before being able to co-sign it.")
            )

        if not is_authenticated_with_an_allowed_plugin(request, submission.form):
            raise PermissionDenied(
                _(
                    "You need to be logged in with one of the allowed authentication backends to co-sign the submission."
                )
            )

        serializer = CosignValidationSerializer(
            data={
                "completed": submission.is_completed,
                "privacy_policy_accepted": request.data["privacy_policy_accepted"],
                "statement_of_truth_accepted": request.data.get(
                    "statement_of_truth_accepted", False
                ),
            },
            context={"request": request, "submission": submission},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # dispatch signal for modules to tap into
        submission_cosigned.send(
            sender=self.__class__, instance=submission, request=self.request
        )

        remove_submission_from_session(submission, self.request.session)

        transaction.on_commit(
            lambda: on_post_submission_event(
                submission.id, PostSubmissionEvents.on_cosign_complete
            )
        )

        out_serializer = SubmissionReportUrlSerializer(
            instance=submission, context={"request": request}
        )
        return Response(out_serializer.data)

    @extend_schema(
        summary=_("Complete a submission"),
        request=SubmissionCompletionSerializer,
        responses={
            200: SubmissionCompletionSerializer,
            400: ValidationErrorSerializer,
            403: ExceptionSerializer,
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
        },
    )
    @transaction.atomic()
    @action(detail=True, methods=["post"], url_name="complete")
    def _complete(self, request, *args, **kwargs):
        """
        Mark the submission as completed.

        Submission completion requires that all required steps are completed.

        Note that the processing of the submission runs in the background, and you
        should periodically check the submission status endpoint to check the state.
        Background processing makes sure that:

        * potential appointments are registered
        * a report PDF is generated
        * the submission is persisted to the configured backend
        * payment is initiated if relevant

        Once a submission is completed, it's removed from the submission and time-stamped
        HMAC token URLs are used for subsequent process flow. This means it's no longer
        possible to change or read the submission data (including individual steps).
        This guarantees that the submission is removed from the session without having
        to rely on the client being able to make another call. IF it is detected in the
        status endpoint that a retry is needed, the ID is added back to the session.

        ---
        **Validation errors**

        The validation errors are returned in the usual `invalidParams` structure. The
        following errors can occur:

        * name `privacyPolicyAccepted` - unchecked while accepting it is required
        * name `statementOfTruthAccepted` - unchecked while accepting it is required
        * name `steps[i].nonFieldErrors`:

            * code `blocked` - a logic rule prevents the step from being submitted,
              which blocks the submission as a whole from being completed.
            * code `incomplete` - there is no or incomplete step data submitted for the
              step at this index.

        * name `steps[i].data.*` - validation errors related to the formio components
          in the step data.

        Additionally, if you try to complete a submission that doesn't allow this (due
        to form-level configuration), you will get an HTTP 403 error.

        ---
        """
        submission = self.get_object()
        if submission.form.submission_allowed != SubmissionAllowedChoices.yes:
            raise PermissionDenied(
                detail=_("Submission is not enabled for this form."),
                code="submission-not-allowed",
            )

        # prepare the submission with evaluated logic so that its state can be validated
        submission.load_execution_state()
        check_submission_logic(submission)

        # validate the input + submission state
        serializer = SubmissionCompletionSerializer(
            data={
                # the statement checkboxes don't run validation if they're not provided as
                # input data, but it's weird to require these fields to be sent in the body
                # if configuration dictates that any of them is not required - it would be logical
                # to not send that data in the first place. So, we default them to what that
                # implies: there has not been an explicit acceptance of the statement
                # checkbox.
                "privacy_policy_accepted": False,
                "statement_of_truth_accepted": False,
                **request.data,
            },
            context={"request": self.request, "submission": submission},
        )
        serializer.is_valid(raise_exception=True)

        # all is fine, we can complete it
        status_url = self._complete_submission(submission)
        serializer.save(status_url=status_url)

        return Response(serializer.data)

    @extend_schema(
        summary=_("Get the submission processing status"),
        request=None,
        responses={
            200: SubmissionProcessingStatusSerializer,
            403: ExceptionSerializer,
            429: ExceptionSerializer,
        },
        parameters=[
            OpenApiParameter(
                "token",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description=_("Time-based authentication token"),
                required=True,
            ),
        ],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"(?P<token>[a-z0-9]{1,3}-[\w]{20})/status",
        permission_classes=(SubmissionStatusPermission,),
        throttle_classes=[PollingRateThrottle],
    )
    def status(self, request, *args, **kwargs):
        """
        Obtain the current submission processing status, after completing it.

        The submission is processed asynchronously. Poll this endpoint to receive
        information on the status of this async processing.
        """
        submission = self.get_object()
        status = SubmissionProcessingStatus(request, submission)
        status.ensure_failure_can_be_managed()
        serializer = SubmissionProcessingStatusSerializer(
            instance=status,
            context={"request": request, "view": self},
        )
        return Response(serializer.data)

    @extend_schema(
        summary=_("Suspend a submission"),
        request=SubmissionSuspensionSerializer,
        responses={
            201: SubmissionSuspensionSerializer,
            403: ExceptionSerializer,
            # 400: TODO - schema for errors
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
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

        if not submission.form.suspension_allowed:
            raise PermissionDenied(_("Suspending this form is not allowed."))

        serializer = SubmissionSuspensionSerializer(
            instance=submission,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        suspension_counter.add(
            1,
            attributes={
                "form.name": submission.form.name,
                "form.uuid": str(submission.form.uuid),
            },
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        logevent.submission_details_view_api(self.get_object(), request.user)
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary=_("Summary page data"),
        description=_("Retrieve the data to display in the submission summary page."),
        responses={
            200: SubmissionStepSummarySerializer(many=True),
        },
    )
    @action(detail=True, methods=["get"], url_name="summary", pagination_class=None)
    def summary(self, request, *args, **kwargs):
        submission = self.get_object()
        summary_data = submission.render_summary_page()
        return Response(summary_data)


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
        responses={
            200: SubmissionStepSerializer,
            403: ExceptionSerializer,
        },
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
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [
        ActiveSubmissionPermission,
        FormAuthenticationPermission,
        CanNavigateBetweenSubmissionStepsPermission,
    ]
    lookup_url_kwarg = "step_uuid"
    submission_url_kwarg = "submission_uuid"
    parser_classes = [IgnoreDataAndConfigFieldCamelCaseJSONParser]
    renderer_classes = [IgnoreDataAndConfigJSONRenderer]

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
        step_uuid = self.kwargs["step_uuid"]
        if not isinstance(step_uuid, UUID):
            step_uuid = UUID(step_uuid)

        # we need to obtain the submission instance (which must exist!) and the
        # form with related data, as efficiently as possible.
        submission_qs = Submission.objects.select_related("form", "auth_info").annotate(
            _form_login_required=Exists(
                FormStep.objects.filter(
                    form_definition__login_required=True, form=OuterRef("form__pk")
                )
            )
        )
        submission = get_object_or_404(submission_qs, uuid=submission_uuid)
        # leverage the execution state which paints a complete picture of the (submitted)
        # steps, including instances that haven't been saved to the DB yet. This is used
        # throughout the different endpoints, so the benefit is that we save a lot of
        # repeated calls due to the internal caching.
        state = submission.load_execution_state()
        submission_step = next(
            (
                step
                for step in state.submission_steps
                if step.form_step.uuid == step_uuid
            ),
            None,
        )
        if submission_step is None:
            raise NotFound(_("Invalid form step reference given."))
        self.check_object_permissions(self.request, submission_step)

        submission = submission_step.submission
        with cleanup_deactivated_form_session(self.request, submission):
            check_form_status(self.request, submission.form)

        return submission_step

    @extend_schema(
        summary=_("Store submission step data"),
        responses={
            200: SubmissionStepSerializer,
            201: SubmissionStepSerializer,
            400: ValidationErrorSerializer,
            403: ExceptionSerializer,
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
        },
    )
    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        """
        The submission data is either created or updated, depending on whether there was
        submission data present before or not. Make sure to retrieve the step data to
        display already filled out fields.

        Note that the form step configuration is currently not validated - this may change
        in the future. I.e. - a step that is marked as not available will still be submitted
        at the time being.
        """
        instance, serializer = self._validate_step_input(request)
        create = instance.pk is None
        serializer.save()

        logevent.submission_step_fill(instance)
        attach_uploads_to_submission_step(instance)

        # See #1480 - if there is navigation between steps and original form field values
        # are changed, they can cause subsequent steps to be not-applicable. If that
        # happens, we need to wipe the data from those steps.
        submission = instance.submission
        # The endpoint permission evaluated the submission state, but now a step has been
        # created/updated, so we need to refresh it
        execution_state = submission.load_execution_state(refresh=True)
        current_step_index = execution_state.submission_steps.index(instance)
        subsequent_steps = execution_state.submission_steps[current_step_index + 1 :]
        for subsequent_step in subsequent_steps:
            if not subsequent_step.pk:
                continue

            # evaluate the logic to determine if the step is applicable or not
            evaluate_form_logic(submission, subsequent_step)
            if not subsequent_step.is_applicable and subsequent_step.completed:
                subsequent_step.reset()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        assert instance.form_step is not None
        step_saved_counter.add(
            1,
            attributes={
                "step.name": instance.form_step.form_definition.name,
                "step.number": current_step_index + 1,
                "type": "create" if create else "update",
                "form.name": submission.form.name,
                "form.uuid": str(submission.form.uuid),
            },
        )

        status_code = status.HTTP_200_OK if not create else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)

    @extend_schema(
        summary=_("Store submission step data"),
        request=SubmissionStepSerializer,
        responses={
            204: None,
            400: ValidationErrorSerializer,
            403: ExceptionSerializer,
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
        },
    )
    @action(detail=True, methods=["post"])
    def validate(self, request, *args, **kwargs):
        """
        Validate the submission step data before persisting.

        This endpoint runs the same validation logic as the PUT endpoint to store the
        data. For invalid data, you will get an HTTP 400 response with error details.
        """
        self._validate_step_input(request)
        # if no validation errors were raised, signal an OK to the client
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _validate_step_input(
        self, request
    ) -> tuple[SubmissionStep, SubmissionStepSerializer]:
        instance = self.get_object()
        create = instance.pk is None
        if create:
            instance.uuid = SubmissionStep._meta.get_field("uuid").default()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return instance, serializer

    @extend_schema(
        summary=_("Apply/check form logic"),
        description=_("Apply/check the logic rules specified on the form step."),
        request=FormDataSerializer,
        responses={
            200: SubmissionStateLogicSerializer,
            403: ExceptionSerializer,
            FormDeactivated.status_code: ExceptionSerializer,
            FormMaintenance.status_code: ExceptionSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="_check-logic",
        throttle_classes=[PollingRateThrottle],
    )
    def logic_check(self, request, *args, **kwargs):
        submission_step = self.get_object()
        submission = submission_step.submission

        form_data_serializer = FormDataSerializer(data=request.data)
        form_data_serializer.is_valid(raise_exception=True)

        if data := form_data_serializer.validated_data["data"]:
            new_configuration = evaluate_form_logic(submission, submission_step, data)
            submission_step.form_step.form_definition.configuration = new_configuration

        submission_state_logic_serializer = SubmissionStateLogicSerializer(
            instance=SubmissionStateLogic(submission=submission, step=submission_step),
            context={
                "request": request,
                "current_step": submission_step,
                "unsaved_data_only": True,
            },
        )
        return Response(submission_state_logic_serializer.data)
