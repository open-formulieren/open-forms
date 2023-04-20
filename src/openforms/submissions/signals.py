import logging

from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.dispatch import Signal, receiver

from openforms.submissions.models import SubmissionReport

logger = logging.getLogger(__name__)


# custom signal to decouple actions done by feature modules - this avoids having to
# import specific module functionality and also allows third party apps/extensions to
# tap into certain events.

submission_start = Signal()
"""
Signal creation of a new :class:`openforms.models.Submission` instance.

Provides:
    :arg instance: The :class:`openforms.models.Submission` instance created.
    :arg request: the HttpRequest instance (or DRF wrapper around it).
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
# TODO document


@receiver(post_delete, sender=SubmissionReport)
def delete_submission_report_files(
    sender: ModelBase, instance: SubmissionReport, **kwargs
) -> None:
    logger.debug("Deleting file %r", instance.content.name)

    instance.content.delete(save=False)
