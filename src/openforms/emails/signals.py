import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from django_yubin.models import Message

from openforms.logging import logevent
from openforms.submissions.models import Submission

from .constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def yubin_messages_status_change_handler(signal, sender, instance, created, **kwargs):
    if created:
        return

    message = instance.get_email_message()
    has_submission = (
        message.extra_headers.get(X_OF_CONTENT_TYPE_HEADER, "")
        == EmailContentTypeChoices.submission
    )
    if not has_submission:
        return

    submission_uuid = message.extra_headers.get(X_OF_CONTENT_UUID_HEADER)
    assert submission_uuid
    event = message.extra_headers.get(X_OF_EVENT_HEADER)

    status_label = instance.get_status_display()
    submission = Submission.objects.filter(uuid=submission_uuid).first()
    if not submission:
        logger.debug(
            "The status of the email for the event %s for submission %s has changed to %s. However, the submission no longer exists.",
            event,
            submission_uuid,
            status_label,
        )
        return

    logevent.email_status_change(submission, event, instance.status, status_label, True)
