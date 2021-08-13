from email.utils import make_msgid
from typing import Tuple

from django.core.mail import EmailMultiAlternatives, get_connection


def send_mail_plus(
    subject,
    message,
    from_email,
    recipient_list,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
    html_message=None,
    attachments=None,
) -> Tuple[str, int]:

    """
    modified copy of django.core.mail.send_mail() with:
    - attachment support
    - returns 'Message-ID' header
    """

    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    message_id = make_msgid()
    headers = {"Message-ID": message_id}
    mail = EmailMultiAlternatives(
        subject,
        message,
        from_email,
        recipient_list,
        headers=headers,
        connection=connection,
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    if attachments:
        for filename, content, mime_type in attachments:
            mail.attach(filename, content, mime_type)
    return message_id, mail.send()
