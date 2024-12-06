import logging

from django.views.generic import RedirectView

from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.models import Submission
from openforms.submissions.views import ResumeFormMixin

from .tokens import submission_appointment_token_generator

logger = logging.getLogger(__name__)


class VerifyCancelAppointmentLinkView(ResumeFormMixin, RedirectView):
    token_generator = submission_appointment_token_generator

    def get_form_resume_url(self, submission: Submission) -> str:
        return get_frontend_redirect_url(
            submission,
            action="afspraak-annuleren",
            action_params={
                "time": submission.appointment_info.start_time.isoformat(),
                "submission_uuid": str(submission.uuid),
            },
        )
