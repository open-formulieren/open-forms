import uuid
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import Iterable

from django_yubin.models import Message

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.utils import get_filtered_submission_admin_url


@dataclass
class FailedEmail:
    submission_uuid: uuid.UUID
    event: str


@dataclass
class FailedRegistration:
    form_uuid: uuid.UUID
    form_name: str
    failed_submissions_counter: int
    initial_failure_at: datetime
    last_failure_at: datetime
    admin_link: str


def collect_failed_emails(since: datetime) -> Iterable[FailedEmail]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__status=Message.STATUS_FAILED,
        extra_data__include_in_daily_digest=True,
    ).distinct("content_type", "extra_data__status", "extra_data__event")

    if not logs:
        return []

    failed_emails = [
        {
            "submission_uuid": log.content_object.uuid,
            "event": log.extra_data["event"],
        }
        for log in logs
    ]

    return failed_emails


def collect_failed_registrations(since: datetime) -> Iterable[FailedRegistration]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event="registration_failure",
    ).order_by("timestamp")

    if not logs:
        return []

    form_sorted_logs = sorted(logs, key=lambda x: x.content_object.form.id)

    grouped_logs = {}
    for form, logs_group in groupby(
        form_sorted_logs, key=lambda log: log.content_object.form
    ):
        grouped_logs[form] = list(logs_group)

    failed_registrations = {}
    for form, submission_logs in grouped_logs.items():
        timestamps = [log.timestamp for log in submission_logs]
        failed_registrations[str(form.uuid)] = {
            "form_name": form.name,
            "failed_submissions_counter": len(submission_logs),
            "initial_failure_at": min(timestamps),
            "last_failure_at": max(timestamps),
            "admin_link": get_filtered_submission_admin_url(form.id, 1, "24hAgo"),
        }

    return list(failed_registrations.values())
