import logging

from django.utils.translation import gettext_lazy as _

from openforms.celery import app

from ..models import Submission, SubmissionReport

__all__ = ["generate_submission_report"]

from ...logging import logevent

logger = logging.getLogger(__name__)


@app.task(bind=True)
def generate_submission_report(task, submission_id: int) -> None:
    logger.debug("Generating submission report for submission %d", submission_id)
    submission = Submission.objects.get(id=submission_id)

    # idempotency: check if there already is a report!
    try:
        submission_report = submission.report
    except SubmissionReport.DoesNotExist:
        submission_report = SubmissionReport.objects.create(
            title=_("%(title)s: Submission report") % {"title": submission.form.name},
            submission=submission,
            task_id=task.request.id,
        )
    # idempotency: check if there already is a report PDF!
    if submission_report.content:
        logevent.pdf_generation_skip(submission, submission_report)
        logger.debug("Submission report PDF was already generated, skipping...")
        return

    logevent.pdf_generation_start(submission)
    try:
        submission_report.generate_submission_report_pdf()
    except Exception as e:
        logevent.pdf_generation_failure(submission, submission_report, e)
        raise
    else:
        logevent.pdf_generation_success(submission, submission_report)
