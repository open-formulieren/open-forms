import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from openforms.submissions.utils import add_submmission_to_session

from .tokens import submission_appointment_token_generator

logger = logging.getLogger(__name__)


class VerifyCancelAppointmentLinkView(RedirectView):
    def get_redirect_url(self, submission_uuid: uuid, token: str, *args, **kwargs):
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Cancel url is not valid")

        # Check that the token is valid
        valid = submission_appointment_token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
            raise PermissionDenied("Cancel url is not valid")

        add_submmission_to_session(submission, self.request.session)

        f = furl(submission.form_url)
        f /= "afspraak-annuleren"
        f.add(
            {
                "time": submission.appointment_info.start_time.isoformat(),
                "submission_uuid": str(submission.uuid),
            }
        )
        return f.url
