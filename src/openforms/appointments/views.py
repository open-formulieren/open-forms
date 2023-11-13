import logging

from django.views.generic import RedirectView

from openforms.authentication.service import FORM_AUTH_SESSION_KEY, store_auth_details
from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.models import Submission
from openforms.submissions.views import ResumeFormMixin

from .tokens import submission_appointment_token_generator
from .utils import find_first_appointment_step

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


class VerifyChangeAppointmentLinkView(ResumeFormMixin, RedirectView):
    token_generator = submission_appointment_token_generator

    def custom_submission_modifications(self, submission: Submission) -> Submission:
        # note that we need to ensure the plain text auth attribute value needs to be set again
        # for machinery relying on it to work. hashes are one-way, so we need to use the session
        # data.
        new_submission = Submission.objects.copy(submission)
        if (form_auth := self.request.session.get(FORM_AUTH_SESSION_KEY)) is not None:
            store_auth_details(new_submission, form_auth)
        return new_submission

    def get_form_resume_url(self, submission: Submission) -> str:
        next_step = find_first_appointment_step(submission.form)
        # simplified flow for new-style appointments
        if submission.form.is_appointment:
            raise RuntimeError(
                "New style appointments do not support the change appointment flow."
            )

        if next_step is None:
            # Should not happen but redirect to first step if it does
            logger.warning(
                "Could not find the appointment step for submission %s,"
                "redirecting user to first step in form",
                submission.uuid,
            )
            next_step = submission.form.formstep_set.first()

        assert next_step is not None, "Form has no steps to redirect to!"

        return get_frontend_redirect_url(
            submission,
            action="resume",
            action_params={
                "step_slug": next_step.slug,
                "submission_uuid": str(submission.uuid),
            },
        )
