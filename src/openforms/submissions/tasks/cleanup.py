from datetime import timedelta

from django.db import transaction
from django.test import RequestFactory
from django.utils import timezone

from rest_framework.request import Request

from openforms.celery import app

from ..constants import RegistrationStatuses
from ..models import Submission
from ..status import SubmissionProcessingStatus
from ..tokens import submission_status_token_generator

__all__ = [
    "cleanup_on_completion_results",
    "finalize_completion_retry",
    "maybe_hash_identifying_attributes",
]


# sync this with the token generator - after this number of days tokens are invalidated
# and the status can no longer be checked. Note that the token generator is the
# "minimum" number of days and the maximum is +1 of that value, because the time
# resolution is up until midnight. See the base token generator docstrings for more
# information.
RETAIN_RESULTS_NUM_DAYS = submission_status_token_generator.token_timeout_days + 1


@app.task(ignore_result=True)
def cleanup_on_completion_results():
    """
    Ensure that celery task execution results are removed from the result backend.

    Celery tasks store their result in the result backend (unless ``ignore_result=True``
    is configured), and take up resources. Results should be consumed through
    :meth:`celery.result.AsyncResult.get` or :meth:`celery.result.AsyncResult.forget`,
    which will remove them from the backend.

    Note that we can only do that for submissions which don't need no further status
    check processing.
    """
    rf = RequestFactory()
    dummy_request = Request(rf.get("/dummy"))

    cutoff = timezone.now() - timedelta(days=RETAIN_RESULTS_NUM_DAYS)

    submissions = Submission.objects.filter(
        # only consider submissions that are completed and old enough
        completed_on__lte=cutoff,
        suspended_on__isnull=True,
        # only clean up submissions that have task_ids stored (prevent re-processing)
        on_completion_task_ids__len__gt=0,
    )

    for submission in submissions:
        processing_status = SubmissionProcessingStatus(
            submission=submission, request=dummy_request
        )
        with transaction.atomic():
            processing_status.forget_results()
            submission.on_completion_task_ids = []
            submission.save(update_fields=["on_completion_task_ids"])


@app.task(ignore_result=True)
def finalize_completion_retry(submission_id: int):
    """
    Finalize of the on_completion_retry workflow.

    This task must be called last and mark the submission as not requiring any retries
    anymore. Tasks being retried that fail again should result in a celery failure
    to prevent this finalizer from running.

    All other internal state will have been updated by the specific (sub)tasks.
    """
    submission = Submission.objects.get(id=submission_id)
    submission.needs_on_completion_retry = False
    submission.save(update_fields=["needs_on_completion_retry"])


@app.task(ignore_result=True)
def maybe_hash_identifying_attributes(submission_id: int):
    """
    If the registration was successful or not relevant, hash the identifying attributes.

    The identifying attributes are used in registration backends which run
    asynchronously, so hashing them can only be done once registration succeeded.
    See #1395 and #1367.
    """
    submission = Submission.objects.get(id=submission_id)
    assert submission.completed_on is not None, "Submission must be completed first"

    # success is set if it succeeded or there was no registration backend configured
    if submission.registration_status != RegistrationStatuses.success:
        return

    if submission.auth_attributes_hashed:
        return

    submission.hash_identifying_attributes(save=True)
