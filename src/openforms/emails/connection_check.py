import dataclasses
from collections.abc import Sequence
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _


@dataclasses.dataclass()
class LabelValue:
    label: str
    value: Any


@dataclasses.dataclass()
class MailCheckResult:
    recipients: Sequence[str]
    sender: str
    success: bool
    backend: str
    feedback: list[str | LabelValue] = dataclasses.field(default_factory=list)
    exception: Exception | None = None

    @property
    def recipients_str(self):
        return ", ".join(self.recipients)


def check_email_backend(recipients: Sequence[str]) -> MailCheckResult:
    if not recipients:
        raise ValueError("recipients must be a list of email-addresses")

    if isinstance(recipients, str):
        recipients = [recipients]

    result = MailCheckResult(
        recipients=recipients,
        sender=settings.DEFAULT_FROM_EMAIL,
        success=False,
        backend=settings.EMAIL_BACKEND,
    )
    uses_yubin = "yubin" in result.backend

    if uses_yubin:
        try:
            from django_yubin import settings as yubin_settings

            result.feedback.append(_("Django-yubin detected:"))
            result.feedback.append(
                LabelValue("MAILER_USE_BACKEND", yubin_settings.USE_BACKEND)
            )
            result.feedback.append(
                LabelValue("MAILER_PAUSE_SEND", yubin_settings.PAUSE_SEND)
            )
            result.feedback.append(
                LabelValue("MAILER_TEST_MODE", yubin_settings.MAILER_TEST_MODE)
            )
            if yubin_settings.MAILER_TEST_MODE:
                result.feedback.append(
                    LabelValue("MAILER_TEST_EMAIL", yubin_settings.MAILER_TEST_EMAIL)
                )
        except ImportError:
            pass

    try:
        send_mail(
            subject=_("Open Forms email configuration test"),
            message=_(
                "If you've received this message the email configuration is setup correctly."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception as e:
        result.feedback.append(
            _("Exception while trying to send test message to %(recipients)s")
            % {"recipients": result.recipients_str}
        )
        result.exception = e
    else:
        result.success = True
        result.feedback.append(
            _(
                "Successfully sent test message to %(recipients)s, please check the mailbox."
            )
            % {"recipients": result.recipients_str}
        )
        if uses_yubin:
            result.feedback.append(
                _(
                    "If the message doesn't arrive check the Django-yubin queue and cronjob."
                )
            )

    return result
