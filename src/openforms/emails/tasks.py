from datetime import timedelta

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_yubin.models import Message

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.logging.models import TimelineLogProxy

from .utils import send_mail_html


@app.task
def send_email_digest() -> None:
    config = GlobalConfiguration.get_solo()
    if not (recipients := config.recipients_email_digest):
        return

    period_start = timezone.now() - timedelta(days=1)

    logs = TimelineLogProxy.objects.filter(
        template="logging/events/email_status_change.txt",
        timestamp__gt=period_start,
        extra_data__status=Message.STATUS_FAILED,
    ).distinct("content_type", "extra_data__status", "extra_data__event")

    if not logs.count():
        return

    content = render_to_string(
        "emails/digest.html",
        {
            "logs": [
                {
                    "submission_uuid": log.content_object.uuid,
                    "event": log.extra_data["event"],
                }
                for log in logs
            ],
        },
    )

    send_mail_html(
        _("[Open Forms] Daily summary of failed emails"),
        content,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
    )
