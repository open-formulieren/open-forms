from uuid import UUID

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from openforms.api.permissions import TimestampedTokenPermission

from ..constants import SUBMISSIONS_SESSION_KEY
from ..form_logic import check_submission_logic
from ..models import SubmissionStep, TemporaryFileUpload
from ..tokens import submission_status_token_generator
from .validation import is_step_unexpectedly_incomplete


def owns_submission(request: Request, submission_uuid: str | UUID) -> bool:
    # The assumption is that auth plugin requirements like LoA
    # MUST be checked upon/before adding the submission uuid to the session
    # therefore "owning a submission" means those requirements were met.
    active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    # Use str so this works with both UUIDs and UUIDs in string format
    return str(submission_uuid) in active_submissions


class AnyActiveSubmissionPermission(permissions.BasePermission):
    """
    Verify that there is at least one active submission for the user session.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if getattr(view, "action", None) in ("create",):
            return True

        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)
        if not active_submissions:
            return False

        return True


class FormAuthenticationPermission(permissions.BasePermission):
    """
    Check that the submission authentication matches the form requirement.

    If the form requires authentication, then permission is not granted if the
    submission has not been authenticated.
    """

    def has_object_permission(
        self, request: Request, view: APIView, step: SubmissionStep
    ) -> bool:
        # ⚡️ form_login_required leverages the optimized viewset query
        login_required = step.submission.form_login_required
        if not login_required:
            return True
        return step.submission.is_authenticated


class ActiveSubmissionPermission(AnyActiveSubmissionPermission):
    """
    Check that the submission matches one of the active submission set on the user session.

    Additionally, provides a method to filter the queryset against the active submissions, which
    can be re-used in API views/viewsets.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        default_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        submission_url_kwarg = getattr(view, "submission_url_kwarg", default_url_kwarg)

        submission_uuid = view.kwargs[submission_url_kwarg]
        return owns_submission(request, submission_uuid)

    def filter_queryset(self, request: Request, view: APIView, queryset):
        active_submissions = request.session.get(SUBMISSIONS_SESSION_KEY)
        if not active_submissions:
            return queryset.none()
        return queryset.filter(uuid__in=active_submissions)


class OwnsTemporaryUploadPermission(AnyActiveSubmissionPermission):
    """
    Verify the upload is registered in the users session
    """

    def has_object_permission(
        self, request: Request, view: APIView, obj: TemporaryFileUpload
    ) -> bool:
        submission_uuid = str(obj.submission.uuid)
        return owns_submission(request, submission_uuid)


class SubmissionStatusPermission(TimestampedTokenPermission):
    token_generator = submission_status_token_generator


class CanNavigateBetweenSubmissionStepsPermission(permissions.BasePermission):
    """
    Check if the user is allowed to interact with a submission step if the previous submission steps are not completed.
    """

    def has_object_permission(
        self, request: Request, view: APIView, obj: SubmissionStep
    ) -> bool:
        user = request.user

        order = obj.form_step.order
        if user.is_staff and user.has_perm("forms.change_form"):
            return True

        # If it's the first step in the form, then it can always be accessed
        if order == 0:
            return True

        submission = obj.submission
        state = submission.load_execution_state()
        check_submission_logic(submission)

        incomplete_steps = [
            submission_step
            for submission_step in state.submission_steps[:order]
            if is_step_unexpectedly_incomplete(submission_step)
        ]

        submission.clear_execution_state()

        if not incomplete_steps:
            return True

        return False
