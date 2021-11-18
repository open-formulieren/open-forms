import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.views.generic import RedirectView

from furl import furl

from openforms.submissions.models import Submission, SubmissionStep
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


class VerifyChangeAppointmentLinkView(RedirectView):
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

        # Create a new submission
        new_submission = Submission.objects.create(
            form=submission.form,
            form_url=submission.form_url,
            previous_submission=submission,
        )
        for submission_step in submission.submissionstep_set.all():
            SubmissionStep.objects.create(
                submission=new_submission,
                form_step=submission_step.form_step,
                data=submission_step.data,
            )

        add_submmission_to_session(new_submission, self.request.session)

        # Find the step url to redirect to
        step_url = ""
        for form_step in submission.form.formstep_set.all():
            for component in form_step.form_definition.configuration["components"]:
                if component.get("appointments", {}).get("showProducts"):
                    step_url = form_step.form_definition.slug

        if not step_url:
            # Should never happen but log in case it does
            logger.warning(
                "Could not find the appointment step for submission %s,"
                "redirecting user to first step in form",
                submission.uuid,
            )
            step_url = submission.form.formstep_set.first().form_definition.slug

        f = furl(new_submission.form_url)
        f /= "stap"
        f /= step_url
        try:
            f.add(
                {
                    "product": submission.get_merged_appointment_data()[
                        "productIDAndName"
                    ]["value"]["identifier"]
                }
            )
        except KeyError:
            # Should not happen but don't want to break flow in case it does
            logger.warning(
                "Could not find product identifier for submission %s", submission.uuid
            )

        return f.url
