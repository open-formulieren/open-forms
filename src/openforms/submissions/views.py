import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl
from rest_framework.reverse import reverse

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY

from .models import Submission
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
