import logging

from django.db.models import F
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.dispatch import Signal, receiver
from django.utils import timezone

from openforms.forms.models.form_statistics import FormStatistics
from openforms.submissions.models import Submission, SubmissionReport

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
"""
Signal that a :class:`openforms.models.Submission` instance has been co-signed.

Provides:
    :arg submission: the :class:`openforms.models.Submission` instance.
    :arg request: the HttpRequest instance (or DRF wrapper around it).
"""


@receiver(post_delete, sender=SubmissionReport)
def delete_submission_report_files(
    sender: ModelBase, instance: SubmissionReport, **kwargs
) -> None:
    logger.debug("Deleting file %r", instance.content.name)

    instance.content.delete(save=False)


@receiver(submission_complete, dispatch_uid="submission.increment_form_counter")
def increment_form_counter(sender, instance: Submission, **kwargs):
    submitted_form = instance.form

    # TODO
    # Replace get_or_create with update_or_create and do this in one block
    # (needs Django v5.2+)
    form_statistics, created = FormStatistics.objects.get_or_create(
        form=submitted_form,
        defaults={
            "form": submitted_form,
            "form_name": submitted_form.name,
            "submission_count": 1,
            "last_submission": timezone.now(),
        },
    )

    if not created:
        form_statistics.form_name = submitted_form.name
        form_statistics.submission_count = F("submission_count") + 1
        form_statistics.last_submission = timezone.now()
        form_statistics.save()
