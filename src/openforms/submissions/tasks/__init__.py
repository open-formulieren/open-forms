# ruff: noqa: F403 F405
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

import structlog
from celery import chain
from celery.result import AsyncResult

from openforms.appointments.tasks import maybe_register_appointment
from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.formio.tasks import execute_component_pre_registration_group

from ..constants import PostSubmissionEvents, RegistrationStatuses
from ..models import PostCompletionMetadata, Submission
from .cleanup import *
from .emails import *
from .payments import *
from .pdf import *
from .registration import *
from .user_uploads import *

logger = structlog.stdlib.get_logger(__name__)


def on_post_submission_event(submission_id: int, event: PostSubmissionEvents) -> None:
    """
    Celery chain of tasks to execute on a submission completion or post completion event.

    This SHOULD be invoked as a transaction.on_commit(...) handler, therefore it should
    not execute any extra queries in the process this function is running in.
    """
    # this can run any time because they have been claimed earlier
    cleanup_temporary_files_for.delay(submission_id)

    # Register an appointment if the submission is for a form which is configured to create appointments.
    register_appointment_task = maybe_register_appointment.si(submission_id)

    # Perform any pre-registration task specified by the registration plugin. If no registration plugin is configured,
    # just set a submission reference (if it hasn't already been set)
    pre_registration_task = pre_registration.si(submission_id, event)

    component_pre_registration_group = execute_component_pre_registration_group.si(
        submission_id
    )

    # Generate the submission report. Contains information about the payment and co-sign status.
    generate_report_task = generate_submission_report.si(submission_id)

    # Attempt registering submission
    register_submission_task = register_submission.si(submission_id, event)

    # Payment status update
    payment_status_update_task = update_submission_payment_status.si(
        submission_id, event
    )

    # Finalise completion: schedule confirmation emails and maybe hash identifying attributes
    finalise_completion_task = finalise_completion.si(submission_id)

    actions_chain = chain(
        register_appointment_task,
        pre_registration_task,
        component_pre_registration_group,
        generate_report_task,
        register_submission_task,
        payment_status_update_task,
        finalise_completion_task,
    )

    async_result: AsyncResult = actions_chain.delay()

    # obtain all the task IDs so we can check the state later
    task_ids = async_result.as_list()

    # NOTE - this is "risky" since we're running outside of the transaction (this code
    # should run in transaction.on_commit)!
    if event == PostSubmissionEvents.on_completion:
        # Case in which an exception was raised that aborts the chain and the user has to try to resubmit the form.
        PostCompletionMetadata.objects.filter(
            submission_id=submission_id,
            trigger_event=PostSubmissionEvents.on_completion,
        ).delete()

    PostCompletionMetadata.objects.create(
        tasks_ids=task_ids,
        submission_id=submission_id,
        trigger_event=event,
    )


@app.task(ignore_result=True)
def retry_processing_submissions():
    """
    Retry submissions that have failed processing before and are recent enough.
    """
    retry_time_limit = timezone.now() - timedelta(
        hours=settings.RETRY_SUBMISSIONS_TIME_LIMIT
    )
    for submission in Submission.objects.filter(
        needs_on_completion_retry=True,
        completed_on__gte=retry_time_limit,
    ):
        logger.debug(
            "retry_start",
            action="submissions.retry_processing",
            submission_uuid=str(submission.uuid),
        )
        on_post_submission_event(submission.pk, PostSubmissionEvents.on_retry)


@app.task()
def finalise_completion(submission_id: int) -> None:
    """
    Schedule all the tasks that need to happen to finalize the submission completion.

    Finalization happens _after_ the confirmation screen is shown to the end-user.
    Showing this screen depends on all the previous registration tasks being completed,
    so the :func:`on_post_submission_event` handler must kick this off AND have its own task ID
    that finishes, which is checked in the submission status endpoint.
    """
    submission = Submission.objects.get(id=submission_id)
    config = GlobalConfiguration.get_solo()

    # The chain should retry if the (pre-)registration failed or if the payment status update failed.
    has_registration_failure = (
        submission.registration_status == RegistrationStatuses.failed
        or (
            submission.payment_required
            and submission.payment_user_has_paid
            and not submission.payment_registered
        )
    )
    if has_registration_failure:
        submission.needs_on_completion_retry = (
            submission.registration_attempts < config.registration_attempt_limit
        )

    # The task should not retry if the registration succeeded and, in the case that payment was required, the
    # payment status update succeeded.
    has_registration_success = (
        (
            submission.registration_status == RegistrationStatuses.success
            and submission.payment_user_has_paid
            and submission.payment_registered
        )
        if submission.payment_required
        else submission.registration_status == RegistrationStatuses.success
    )
    if has_registration_success:
        submission.needs_on_completion_retry = False

    submission.save(update_fields=["needs_on_completion_retry"])

    schedule_emails_task = schedule_emails.si(submission_id)
    schedule_emails_task.delay()

    hash_identifying_attributes_task = maybe_hash_identifying_attributes.si(
        submission_id
    )
    hash_identifying_attributes_task.delay()
