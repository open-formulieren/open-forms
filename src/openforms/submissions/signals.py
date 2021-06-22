import logging

from django.db.models.base import ModelBase
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from openforms.submissions.models import SubmissionReport

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=SubmissionReport)
def delete_submission_report_files(
    sender: ModelBase, instance: SubmissionReport, **kwargs
) -> None:
    logger.debug("Deleting file %r" % instance.content.name)

    instance.content.delete()
