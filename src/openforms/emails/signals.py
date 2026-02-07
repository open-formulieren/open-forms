from django.db.models.signals import post_save
from django.dispatch import receiver

import structlog
from django_yubin.models import Message

from openforms.logging import audit_logger
from openforms.submissions.models import Submission

from .constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
)

logger = structlog.stdlib.get_logger(__name__)


@receiver(post_save, sender=Message)
def yubin_messages_status_change_handler(
    signal, sender, instance: Message, created, **kwargs
):
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
    log = logger.bind(
        message_id=instance.pk,
        submission_uuid=submission_uuid,
        email_event=event,
    )
    audit_log = audit_logger.bind(**structlog.get_context(log))

    status_label = instance.get_status_display()  # pyright: ignore[reportAttributeAccessIssue]
    submission = Submission.objects.filter(uuid=submission_uuid).first()

    if not submission:
        log.debug("email_status_change_submission_not_found", status=status_label)
        return

    audit_log.info(
        "email_status_change",
        new_status=instance.status,
        status_label=str(status_label),
    )
