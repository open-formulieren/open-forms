import logging
import uuid
from urllib.parse import urljoin

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from openforms.submissions.utils import add_submmission_to_session

from .tokens import submission_resume_token_generator

logger = logging.getLogger(__name__)


class ResumeSubmissionView(RedirectView):
    def get_redirect_url(self, submission_uuid: uuid, token: str, *args, **kwargs):
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Resume url is not valid")

        # Check that the token is valid
        valid = submission_resume_token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
            raise PermissionDenied("Resume submission url is not valid")

        add_submmission_to_session(submission, self.request.session)

        config = GlobalConfiguration.get_solo()

        if not config.sdk_url:
            raise RuntimeError("No SDK URL configured")

        f = furl(config.sdk_url)
        # furl adds paths with the /= operator
        f /= "stap"
        f /= submission.get_last_completed_step().form_step.form_definition.slug
        # Add the submission uuid to the query param
        f.add({"submission_uuid": submission.uuid})

        return f.url
