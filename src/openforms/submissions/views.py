import logging
import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from furl import furl
from privates.views import PrivateMediaView
from rest_framework.reverse import reverse

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY

from .constants import RegistrationStatuses
from .models import Submission, SubmissionFileAttachment
from .tokens import submission_resume_token_generator
from .utils import add_submmission_to_session

logger = logging.getLogger(__name__)


class ResumeFormMixin:
    token_generator = None

    def validate_url_and_get_submission(
        self, submission_uuid: uuid, token: str
    ) -> Submission:
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Url is not valid")

        # Check that the token is valid
        valid = self.token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
            raise PermissionDenied("Url is not valid")

        return submission

    def get_form_resume_url(self, submission: Submission) -> str:
        raise NotImplementedError(
            "You must implement the 'get_form_resume_url' method."
        )

    def get_login_url(self, submission: Submission, token: str) -> str:
        auth_start_url = reverse(
            "authentication:start",
            request=self.request,
            kwargs={"slug": submission.form.slug, "plugin_id": submission.auth_plugin},
        )

        redirect_url = furl(auth_start_url)
        redirect_url.args["next"] = reverse(
            self.request.resolver_match.view_name,
            request=self.request,
            kwargs={"submission_uuid": submission.uuid, "token": token},
        )

        return redirect_url.url

    def is_auth_data_correct(self, submission: Submission) -> bool:
        is_auth_plugin_correct = (
            submission.auth_plugin
            == self.request.session[FORM_AUTH_SESSION_KEY]["plugin"]
        )
        submission_auth_value = getattr(
            submission, self.request.session[FORM_AUTH_SESSION_KEY]["attribute"]
        )
        is_auth_data_correct = (
            submission_auth_value
            == self.request.session[FORM_AUTH_SESSION_KEY]["value"]
        )

        return is_auth_plugin_correct and is_auth_data_correct

    def custom_submission_modifications(self, submission: Submission) -> Submission:
        return submission

    def get_redirect_url(
        self, submission_uuid: uuid, token: str, *args, **kwargs
    ) -> str:
        submission = self.validate_url_and_get_submission(submission_uuid, token)

        # No login required, skip authentication
        if not submission.form.login_required:
            submission = self.custom_submission_modifications(submission)
            add_submmission_to_session(submission, self.request.session)
            return self.get_form_resume_url(submission)

        # Login IS required. Check if the user has already logged in.
        # This is done by checking if the authentication details are in the session and
        # if they match those in the saved submission.
        if FORM_AUTH_SESSION_KEY in self.request.session:
            if not self.is_auth_data_correct(submission):
                raise PermissionDenied("Authentication data is not valid")

            submission = self.custom_submission_modifications(submission)
            add_submmission_to_session(submission, self.request.session)
            return self.get_form_resume_url(submission)

        # The user has not logged in. Redirect them to the start of the authentication process
        return self.get_login_url(submission, token)


class ResumeSubmissionView(ResumeFormMixin, RedirectView):
    token_generator = submission_resume_token_generator

    def get_form_resume_url(self, submission: Submission) -> str:
        form_resume_url = furl(submission.form_url)
        # furl adds paths with the /= operator
        form_resume_url /= "stap"
        form_resume_url /= (
            submission.get_last_completed_step().form_step.form_definition.slug
        )
        # Add the submission uuid to the query param
        form_resume_url.add({"submission_uuid": submission.uuid})
        return form_resume_url.url


class SubmissionAttachmentDownloadView(LoginRequiredMixin, PrivateMediaView):
    # only consider finished submissions (those are eligible for further processing)
    # and submissions that have been successfully registered with the registration
    # backend
    queryset = SubmissionFileAttachment.objects.filter(
        submission_step__submission__completed_on__isnull=False,
        submission_step__submission__registration_status=RegistrationStatuses.success,
    )
    # expose UUIDs in URLs instead of enumeration-attack susceptible PKs
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "content"
    permission_required = "submissions.view_submissionfileattachment"

    def has_permission(self):
        if not self.request.user.is_staff:
            return False
        return super().has_permission()

    def get_object(self, queryset=None):
        assert queryset is None, "Code path with explicit queryset not supported"

        # check that a hash parameter is present on the request
        content_hash = self.request.GET.get("hash")
        if not content_hash:
            logger.warning(
                "Unauthorized file download attempted (missing content hash). Path: %s, user: %r",
                self.request.path,
                self.request.user,
            )
            raise PermissionDenied(_("File access denied."))

        # cache the object for future lookups
        if not hasattr(self, "_object"):
            obj = super().get_object(queryset=queryset)

            if not constant_time_compare(obj.content_hash, content_hash):
                logger.warning(
                    "Unauthorized file download attempted (invalid content hash). Path: %s, user: %r",
                    self.request.path,
                    self.request.user,
                )
                raise PermissionDenied(_("File access denied."))

            self._object = obj

        return self._object

    def get_sendfile_opts(self) -> dict:
        submission_attachment = self.get_object()
        opts = {
            "attachment": True,
            "attachment_filename": submission_attachment.file_name,
            "mimetype": submission_attachment.content_type,
        }
        return opts
