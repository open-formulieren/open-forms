from celery import chain
from celery.result import AsyncResult

from openforms.celery import app
from openforms.registrations.tasks import register_submission

from ..models import Submission
from .appointments import *  # noqa
from .emails import *  # noqa
from .payments import *  # noqa
from .pdf import *  # noqa
from .registration import *  # noqa
from .user_uploads import *  # noqa


def on_completion(submission_id: int) -> str:
    """
    Celery chain of tasks to execute on a submission completion event.

    This SHOULD be invoked as a transaction.on_commit(...) handler, therefore it should
    not execute any extra queries in the process this function is running in.
    """
    # use immutable signatures so that the result of previous tasks is not passed
    # in as an argument to chained tasks
    register_appointment_task = maybe_register_appointment.si(submission_id)
    update_appointment_task = maybe_update_appointment.si(submission_id)
    generate_report_task = generate_submission_report.si(submission_id)
    register_submission_task = register_submission.si(submission_id)
    obtain_submission_reference_task = obtain_submission_reference.si(submission_id)
    finalize_completion_task = finalize_completion.si(submission_id)

    # for the orchestration with distributed processing and dependencies between
    # tasks, see the Celery documentation:
    # https://docs.celeryproject.org/en/stable/userguide/canvas.html#guide-canvas
    # Additionally, check the developer documentation of Open Forms for a visual
    # representation of the task orchestration and dependencies (TODO, @joeri)
    # The linked task (= next task) is only executed if the previous task returns
    # successfully, so error handling needs to happen inside each task.
    on_completion_chain = chain(
        # The appointment must be registered before a confirmation PDF is generated and
        # any backend registration happens, as on-failure, the user should get feedback
        # about the failure.
        register_appointment_task,
        # The submission report needs to already have been generated before it can be
        # attached in the registration backend.
        generate_report_task,
        # TODO: ensure that any images that need resizing are done so before this is attempted
        register_submission_task,
        obtain_submission_reference_task,
        update_appointment_task,
        # TODO: initiate payment -> this should probably just generate the link?
        # we schedule the finalization so that the ``async_result`` below is marked
        # as done, which is the "signal" to show the confirmation page. Actual payment
        # flow & confirmation e-mail follow later.
        finalize_completion_task,
    )

    # this can run any time because they have been claimed earlier
    cleanup_temporary_files_for.delay(submission_id)

    async_result: AsyncResult = on_completion_chain.delay()
    # NOTE - this is "risky" since we're running outside of the transaction (this code
    # should run in transaction.on_commit)!
    Submission.objects.filter(id=submission_id).update(
        on_completion_task_id=async_result.id
    )
    return async_result.id


@app.task(bind=True)
def finalize_completion(task, submission_id: int) -> None:
    """
    Schedule all the tasks that need to happen to finalize the submission completion.

    Finalization happens _after_ the confirmation screen is shown to the end-user.
    Showing this screen depends on all the previous registration tasks being completed,
    so the :func:`on_completion` handler must kick this off AND have its own task ID
    that finishes, which is checked in the submission status endpoint.
    """
    send_confirmation_email_task = maybe_send_confirmation_email.si(submission_id)
    send_confirmation_email_task.delay()

    # TODO: clean up session data
