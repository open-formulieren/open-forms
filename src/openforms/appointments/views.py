import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl

from openforms.submissions.models import Submission
from openforms.submissions.utils import add_submmission_to_session

from .tokens import submission_appointment_token_generator
from .utils import find_first_appointment_step

logger = logging.getLogger(__name__)


def validate_url_and_get_submission(submission_uuid: uuid, token: str) -> Submission:
    try:
        submission = Submission.objects.get(uuid=submission_uuid)
    except Submission.DoesNotExist:
        logger.debug(
            "Called endpoint with an invalid submission uuid: %s", submission_uuid
        )
        raise PermissionDenied("Url is not valid")

    # Check that the token is valid
    valid = submission_appointment_token_generator.check_token(submission, token)
    if not valid:
        logger.debug("Called endpoint with an invalid token: %s", token)
        raise PermissionDenied("Url is not valid")

    return submission


class VerifyCancelAppointmentLinkView(RedirectView):
    def get_redirect_url(self, submission_uuid: uuid, token: str, *args, **kwargs):
        submission = validate_url_and_get_submission(submission_uuid, token)

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


class VerifyChangeAppointmentLinkView(RedirectView):
    def get_redirect_url(self, submission_uuid: uuid, token: str, *args, **kwargs):
        submission = validate_url_and_get_submission(submission_uuid, token)

        new_submission = Submission.objects.copy(submission)

        add_submmission_to_session(new_submission, self.request.session)

        next_step = find_first_appointment_step(new_submission.form)

        if next_step is None:
            # Should not happen but redirect to first step if it does
            logger.warning(
                "Could not find the appointment step for submission %s,"
                "redirecting user to first step in form",
                new_submission.uuid,
            )
            next_step = new_submission.form.formstep_set.select_related(
                "form_definition"
            ).first()

        assert next_step is not None, "Form has no steps to redirect to!"

        f = furl(new_submission.form_url)
        f /= "stap"
        f /= next_step.form_definition.slug
        f.add({"submission_uuid": new_submission.uuid})

        return f.url
