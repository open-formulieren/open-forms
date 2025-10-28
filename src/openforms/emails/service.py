from django.core.mail.message import EmailMultiAlternatives

from django_yubin.models import Message

from openforms.submissions.models import Submission

from .constants import (
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
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
    # To narrow down the queryset significantly, we filter on the date created and
    # whether the message contains the relevant submission uuid. For a more detailed
    # report on the performance, see:
    # https://github.com/open-formulieren/open-forms/pull/5409#discussion_r2194706198
    messages = (
        Message.objects.filter(
            date_created__gte=submission.created_on,
            _message_data__contains=str(submission.uuid),
        )
        .order_by("-date_created")
        .iterator()
    )

    for message in messages:
        email = message.get_email_message()
        assert isinstance(email, EmailMultiAlternatives)

        submission_uuid = email.extra_headers.get(X_OF_CONTENT_UUID_HEADER)
        event = email.extra_headers.get(X_OF_EVENT_HEADER)

        if (
            submission_uuid != str(submission.uuid)
            or event != EmailEventChoices.confirmation
        ):
            continue

        html = next(alt[0] for alt in email.alternatives if alt[1] == "text/html")
        assert isinstance(html, str)

        return html, message.pk

    return None
