from django.db import transaction
from django.utils import timezone

from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.logging import logevent

from ..constants import PostSubmissionEvents
from ..models import Submission
from ..signals import submission_complete
from ..tasks import on_post_submission_event
from ..tokens import submission_status_token_generator
from ..utils import persist_user_defined_variables, remove_submission_from_session


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

        token = submission_status_token_generator.make_token(submission)
        status_url = self.request.build_absolute_uri(
            reverse(
                "api:submission-status",
                kwargs={"uuid": submission.uuid, "token": token},
            )
        )

        return status_url
