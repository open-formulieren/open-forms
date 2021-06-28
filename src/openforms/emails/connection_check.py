import dataclasses
import smtplib
import socket
from typing import List, Optional, Sequence

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPEmailBackend
from django.utils.translation import gettext as _


@dataclasses.dataclass()
class SMTPCheckResult:
    recipients: Sequence[str]
    sender: str
    success: bool
    host: str
    port: int
    with_credentials: bool = False
    with_tls: bool = False
    with_ssl: bool = False
    feedback: List[str] = dataclasses.field(default_factory=list)
    email_message: Optional[EmailMessage] = None
    exception: Optional[Exception] = None

    @property
    def recipients_str(self):
        return ", ".join(self.recipients)


def check_smtp_settings(recipients: Sequence[str]) -> SMTPCheckResult:
    if not recipients:
        raise ValueError("recipients must be a list of email-addresses")

    if isinstance(recipients, str):
        recipients = [recipients]

    result = SMTPCheckResult(
        recipients=recipients,
        sender=settings.DEFAULT_FROM_EMAIL,
        success=False,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        with_tls=bool(settings.EMAIL_USE_TLS),
        with_ssl=bool(settings.EMAIL_USE_SSL),
        with_credentials=bool(
            settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD
        ),
    )

    # TODO decide if we want to check if we actually use an SMTP backend (directly or trough django-yubin)

    if not getattr(settings, "EMAIL_HOST", ""):
        result.feedback.append(
            _("Missing required setting %(setting_name)s")
            % {"setting_name": "EMAIL_HOST"}
        )
        return result

    host_str = f"{settings.EMAIL_HOST}:{settings.EMAIL_PORT}"

    result.email_message = EmailMessage(
        subject=_("Open Forms SMTP connection test"),
        body=_(
            "If you've received this message the SMTP connection is configured correctly."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )

    try:
        # INIT
        backend = DjangoSMTPEmailBackend(fail_silently=False, timeout=10)
        try:
            # OPEN
            backend.open()
        except (smtplib.SMTPException, socket.error) as e:
            result.feedback.append(
                _("Cannot connect to host %(host)s") % {"host": host_str}
            )
            result.exception = e
        else:
            try:
                # SEND
                backend.send_messages([result.email_message])
            except smtplib.SMTPException as e:
                result.feedback.append(
                    _("Cannot send test message to %(recipients)s")
                    % {"recipients": result.recipients_str}
                )
                result.exception = e
            else:
                # SUCCESS
                result.feedback.append(
                    _(
                        "Successfully sent test message to %(recipients)s, please check the mailbox."
                    )
                    % {"recipients": result.recipients_str}
                )
                result.success = True
        finally:
            try:
                # CLOSE
                backend.close()
            except smtplib.SMTPException as e:
                result.feedback.append(
                    _("Cannot close connection to host %(host)s") % {"host": host_str}
                )
                result.exception = e
                # reset what might have been set after sending message
                result.success = False

    except ValueError as e:
        result.feedback.append(_("Cannot initialize email backend"))
        result.exception = e

    return result
