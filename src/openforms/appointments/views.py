import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl

from openforms.submissions.models import Submission
from openforms.submissions.views import ResumeFormMixin

from .tokens import submission_appointment_token_generator
from .utils import find_first_appointment_step

logger = logging.getLogger(__name__)


class VerifyCancelAppointmentLinkView(ResumeFormMixin, RedirectView):
    token_generator = submission_appointment_token_generator

    def get_form_resume_url(self, submission: Submission) -> str:
        f = furl(submission.form_url)
        f /= "afspraak-annuleren"
        f.add(
            {
                "time": submission.appointment_info.start_time.isoformat(),
                "submission_uuid": str(submission.uuid),
            }
        )
        return f.url


class VerifyChangeAppointmentLinkView(ResumeFormMixin, RedirectView):
    token_generator = submission_appointment_token_generator

    def custom_submission_modifications(self, submission: Submission) -> Submission:
        return Submission.objects.copy(submission)

    def get_form_resume_url(self, submission: Submission) -> str:
        next_step = find_first_appointment_step(submission.form)

        if next_step is None:
            # Should not happen but redirect to first step if it does
            logger.warning(
                "Could not find the appointment step for submission %s,"
                "redirecting user to first step in form",
                submission.uuid,
            )
            next_step = submission.form.formstep_set.select_related(
                "form_definition"
            ).first()

        assert next_step is not None, "Form has no steps to redirect to!"

        f = furl(submission.form_url)
        f /= "stap"
        f /= next_step.form_definition.slug
        f.add({"submission_uuid": submission.uuid})

        return f.url
