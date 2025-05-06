from django.utils.translation import gettext_lazy as _

import structlog

from openforms.celery import app
from openforms.logging import logevent

from ..models import Submission, SubmissionReport

__all__ = ["generate_submission_report"]


logger = structlog.stdlib.get_logger(__name__)


@app.task(bind=True)
def generate_submission_report(task, submission_id: int) -> None:
    log = logger.bind(
        action="submissions.generate_submission_report", submission_id=submission_id
    )

    log.debug("trigger_submission_report_generation")
    submission = Submission.objects.get(id=submission_id)
    log = log.bind(submission_uuid=str(submission.uuid))

    # idempotency: check if there already is a report!
    try:
        submission_report = submission.report
    except SubmissionReport.DoesNotExist:
        submission_report = SubmissionReport.objects.create(
            title=_("%(title)s: Submission report (%(reference)s)")
            % {
                "title": submission.form.name,
                "reference": submission.public_registration_reference,
            },
            submission=submission,
            task_id=task.request.id,
        )
    # idempotency: check if there already is a report PDF!
    if submission_report.content:
        logevent.pdf_generation_skip(submission, submission_report)
        log.debug("pdf_generation_skip", reason="already_exists")
        return

    log.debug("pdf_generation_start")
    logevent.pdf_generation_start(submission)
    try:
        submission_report.generate_submission_report_pdf()
    except Exception as exc:
        log.warning("pdf_generation_failure", exc_info=exc)
        logevent.pdf_generation_failure(submission, submission_report, exc)
        raise
    else:
        log.debug("pdf_generation_success")
        logevent.pdf_generation_success(submission, submission_report)
