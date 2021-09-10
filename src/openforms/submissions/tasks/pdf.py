import logging

from django.utils.translation import gettext_lazy as _

from openforms.celery import app

from ..models import Submission, SubmissionReport

__all__ = ["generate_submission_report"]

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
            title=_("%(title)s: Submission report")
            % {"title": submission.form.public_name},
            submission=submission,
            task_id=task.request.id,
        )
    # idempotency: check if there already is a report PDF!
    if submission_report.content:
        logger.debug("Submission report PDF was already generated, skipping...")
        return

    submission_report.generate_submission_report_pdf()
