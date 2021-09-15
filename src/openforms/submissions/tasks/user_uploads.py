from datetime import timedelta
from typing import Tuple

from django.conf import settings

from openforms.celery import app

from ..attachments import (
    cleanup_submission_temporary_uploaded_files,
    cleanup_unclaimed_temporary_uploaded_files,
    resize_attachment,
)
from ..models import Submission, SubmissionFileAttachment

__all__ = [
    "cleanup_temporary_files_for",
    "cleanup_unclaimed_temporary_files",
    "resize_submission_attachment",
]


@app.task(ignore_result=True)
def cleanup_temporary_files_for(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    cleanup_submission_temporary_uploaded_files(submission)


@app.task(ignore_result=True)
def cleanup_unclaimed_temporary_files() -> None:
    days = settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS
    cleanup_unclaimed_temporary_uploaded_files(timedelta(days=days))


@app.task(ignore_result=True)
def resize_submission_attachment(attachment_id: int, size: Tuple[int, int]) -> None:
    attachment = SubmissionFileAttachment.objects.get(id=attachment_id)
    resize_attachment(attachment, size)
