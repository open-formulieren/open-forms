from datetime import timedelta

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.registrations.utils import collect_registrations_failures

from .utils import collect_failed_emails, send_mail_html


@app.task
def send_email_digest() -> None:
    config = GlobalConfiguration.get_solo()
    if not (recipients := config.recipients_email_digest):
        return

    desired_period = timezone.now() - timedelta(days=1)

    failed_emails = collect_failed_emails(desired_period)
    failed_registrations = collect_registrations_failures(desired_period)

    if not (failed_emails or failed_registrations):
        return

    content = render_to_string(
        "emails/admin_digest.html",
        {
            "failed_emails": failed_emails,
            "failed_registrations": failed_registrations,
        },
    )

    send_mail_html(
        _("[Open Forms] Daily summary of failed procedures"),
        content,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
    )
