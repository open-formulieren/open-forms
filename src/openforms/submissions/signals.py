from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_delete
from django.dispatch import Signal, receiver

import structlog

from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
)
from openforms.utils.files import _delete_obj_files, get_file_field_names

logger = structlog.stdlib.get_logger(__name__)


# custom signal to decouple actions done by feature modules - this avoids having to
# import specific module functionality and also allows third party apps/extensions to
# tap into certain events.

submission_start = Signal()
"""
Signal creation of a new :class:`openforms.models.Submission` instance.

Provides:
    :arg instance: The :class:`openforms.models.Submission` instance created.
    :arg request: the HttpRequest instance (or DRF wrapper around it).
    :arg anonymous: boolean indicating if the user is logged in or not.
"""

submission_resumed = Signal()
"""
Signal resumption of an existing :class:`openforms.models.Submission` instance.

Provides:
    :arg instance: The :class:`openforms.models.Submission` instance created.
    :arg request: the HttpRequest instance (or DRF wrapper around it).
"""


submission_complete = Signal()
"""
Signal completion of a :class:`openforms.models.Submission` instance.

Provides:
    :arg request: the HttpRequest instance (or DRF wrapper around it).
"""

submission_cosigned = Signal()
"""
Signal that a :class:`openforms.models.Submission` instance has been co-signed.

Provides:
    :arg submission: the :class:`openforms.models.Submission` instance.
    :arg request: the HttpRequest instance (or DRF wrapper around it).
"""


@receiver(post_delete, sender=SubmissionFileAttachment)
def delete_obj_files(
    sender: type[SubmissionFileAttachment], instance: SubmissionFileAttachment, **kwargs
):
    """A ``post_delete`` signal ensuring file deletion on database record deletion.

    The implementation is identical to the :class:`openforms.utils.files.DeleteFileFieldFilesMixin` class,
    and is required as the Django deletion internals might not call the model's ``delete`` in all cases.
    """
    file_field_names = get_file_field_names(sender)
    with transaction.atomic():
        _delete_obj_files(file_field_names, instance)


@receiver(post_delete, sender=SubmissionReport)
def delete_submission_report_files(
    sender: type[SubmissionReport], instance: SubmissionReport, **kwargs
) -> None:
    logger.debug(
        "submissions.delete_submission_report_pdf", filename=instance.content.name
    )

    instance.content.delete(save=False)


@receiver(
    submission_complete, dispatch_uid="submission.increment_submissions_form_counter"
)
def increment_submissions_form_counter(sender, instance: Submission, **kwargs):
    if instance.form.submission_limit:
        instance.form.submission_counter = F("submission_counter") + 1
        instance.form.save(update_fields=("submission_counter",))
