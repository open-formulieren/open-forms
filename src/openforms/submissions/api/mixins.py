from django.db import transaction
from django.utils import timezone

import structlog
from flags.state import flag_disabled
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.logging import logevent

from ..constants import PostSubmissionEvents
from ..metrics import attachments_per_submission, completion_counter
from ..models import Submission, SubmissionFileAttachment
from ..signals import submission_complete
from ..tasks import on_post_submission_event
from ..tokens import submission_status_token_generator
from ..utils import persist_user_defined_variables, remove_submission_from_session

logger = structlog.stdlib.get_logger(__name__)


class SubmissionCompletionMixin:
    request: Request

    def _complete_submission(self, submission: Submission) -> str:
        """
        Mark the submission as completed.

        This encapsulates the logic of what it means to 'complete' a submission,
        ensuring that the relevant metadata is set and post-completion hooks trigger,
        such as scheduling the processing via Celery.
        """

        # dispatch signal for modules to tap into
        submission_complete.send(
            sender=self.__class__, request=self.request, instance=submission
        )

        submission.calculate_price(save=False)
        submission.completed_on = timezone.now()

        # If we have reached the submission completion, all steps were already
        # submitted, so it *shouldn't* be necessary to persist the user-defined
        # variables again. That is why we only execute this if the feature flag is
        # disabled, i.e. return to previous behaviour.
        if flag_disabled("PERSIST_USER_DEFINED_VARIABLES_UPON_STEP_COMPLETION"):
            # This requires form logic to be evaluated, which is done already in the
            # "complete" endpoint of the submission view
            assert getattr(submission, "_form_logic_evaluated", False)
            persist_user_defined_variables(submission)

        # all logic has run; we can fix backend
        submission.save()

        logevent.form_submit_success(submission)

        remove_submission_from_session(submission, self.request.session)

        # after committing the database transaction where the submissions completion is
        # stored, start processing the completion.
        transaction.on_commit(
            lambda: on_post_submission_event(
                submission.pk, PostSubmissionEvents.on_completion
            )
        )
        transaction.on_commit(
            lambda: logger.info(
                "submission_completed", submission_uuid=str(submission.uuid)
            )
        )

        token = submission_status_token_generator.make_token(submission)
        status_url = self.request.build_absolute_uri(
            reverse(
                "api:submission-status",
                kwargs={"uuid": submission.uuid, "token": token},
            )
        )

        form = submission.form
        metric_attributes = {
            "form.uuid": str(form.uuid),
            "form.name": str(form.name),
        }
        completion_counter.add(1, metric_attributes)
        num_attachments = SubmissionFileAttachment.objects.filter(
            submission_step__submission=submission
        ).count()
        attachments_per_submission.record(num_attachments, metric_attributes)

        return status_url
