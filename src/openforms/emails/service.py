from django_yubin.models import Message

from openforms.submissions.models import Submission

from .constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)

__all__ = ["get_last_confirmation_email"]


def get_last_confirmation_email(submission: Submission) -> tuple[str, int] | None:
    """
    Get the last created confirmation email from the
    :class:`django_yubin.models.Message` model.

    :return: A tuple of the HTML content and message ID of the last created confirmation
      email for the specified submission. ``None`` if there weren't any.
    """
    # We only care about messages that were created after the submission
    messages = Message.objects.filter(date_created__gte=submission.created_on).order_by(
        "-date_created"
    )

    for message in messages:
        email = message.get_email_message()

        has_submission = (
            email.extra_headers.get(X_OF_CONTENT_TYPE_HEADER)
            == EmailContentTypeChoices.submission
        )
        if not has_submission:
            continue

        submission_uuid = email.extra_headers.get(X_OF_CONTENT_UUID_HEADER)
        assert submission_uuid

        if (
            submission_uuid != str(submission.uuid)
            or email.extra_headers.get(X_OF_EVENT_HEADER)
            != EmailEventChoices.confirmation
        ):
            continue

        # NOTE - only HTML is supported as an alternative, and we add the HTML content
        # for the confirmation email
        assert len(email.alternatives) == 1
        assert email.alternatives[0][1] == "text/html"

        return email.alternatives[0][0], message.pk

    return None
