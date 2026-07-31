from django.db import transaction
from django.utils import timezone

import structlog
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.logging import audit_logger
from openforms.logging.constants import FORM_SUBMIT_SUCCESS_EVENT

from ..constants import PostSubmissionEvents
from ..metrics import attachments_per_submission, completion_counter
from ..models import Submission, SubmissionFileAttachment
from ..signals import submission_complete
from ..tasks import on_post_submission_event
from ..tokens import submission_status_token_generator
from ..utils import remove_submission_from_session

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

        # all logic has run; we can fix backend
        submission.save()

        audit_logger.info(
            FORM_SUBMIT_SUCCESS_EVENT,
            submission_uuid=str(submission.uuid),
        )

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
