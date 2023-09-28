from django.db.models.signals import post_save
from django.dispatch import receiver

from django_yubin.models import Message

from openforms.logging import logevent
from openforms.submissions.models import Submission

from .constants import X_OF_CONTENT_UUID_HEADER, X_OF_EVENT_HEADER


@receiver(post_save, sender=Message)
def yubin_messages_status_change_handler(signal, sender, instance, created, **kwargs):
    if created:
        return

    message = instance.get_email_message()
    submission_uuid = message.extra_headers.get(X_OF_CONTENT_UUID_HEADER)
    event = message.extra_headers.get(X_OF_EVENT_HEADER)
    if not submission_uuid:
        return

    status_label = instance.get_status_display()
    submission = Submission.objects.filter(uuid=submission_uuid).first()
    if not submission:
        # Maybe add logging in case a submission is deleted before the email is sent?
        return

    logevent.email_status_change(submission, event, status_label)
