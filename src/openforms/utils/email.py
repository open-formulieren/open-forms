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
):
    """
    Send outgoing email.

    modified copy of :func:`django.core.mail.send_mail()` with:

    - attachment support

    """

    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    mail = EmailMultiAlternatives(
        subject, message, from_email, recipient_list, connection=connection
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    if attachments:
        for filename, content, mime_type in attachments:
            mail.attach(filename, content, mime_type)
    return mail.send()
