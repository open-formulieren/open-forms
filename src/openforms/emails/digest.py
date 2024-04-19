import uuid
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_yubin.models import Message
from furl import furl

from openforms.contrib.brk.service import check_brk_config_for_addressNL
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models.submission import Submission
from openforms.submissions.utils import get_filtered_submission_admin_url
from openforms.typing import StrOrPromise


@dataclass
class FailedEmail:
    submission_uuid: uuid.UUID
    event: str


@dataclass
class FailedRegistration:
    form_name: str
    failed_submissions_counter: int
    initial_failure_at: datetime
    last_failure_at: datetime
    admin_link: str
    has_errors: bool


@dataclass
class FailedPrefill:
    plugin_label: str
    form_names: list[str]
    submission_ids: list[str]
    initial_failure_at: datetime
    last_failure_at: datetime
    # whether an uncaught exception has happened or empty data was returned
    has_errors: bool

    @property
    def admin_link(self) -> str:
        content_type = ContentType.objects.get_for_model(Submission).id

        query_params = {
            "content_type": content_type,
            "object_id__in": ",".join(self.submission_ids),
            "extra_data__log_event__in": "prefill_retrieve_empty,prefill_retrieve_failure",
        }
        submissions_admin_url = furl(
            reverse("admin:logging_timelinelogproxy_changelist")
        )
        return submissions_admin_url.add(query_params).url

    @property
    def failed_submissions_counter(self) -> int:
        return len(self.submission_ids)


@dataclass
class BrokenConfiguration:
    config_name: StrOrPromise
    exception_message: str


def collect_failed_emails(since: datetime) -> Iterable[FailedEmail]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__status=Message.STATUS_FAILED,
        extra_data__include_in_daily_digest=True,
    ).distinct("content_type", "extra_data__status", "extra_data__event")

    if not logs:
        return []

    failed_emails = [
        FailedEmail(
            submission_uuid=log.content_object.uuid, event=log.extra_data["event"]
        )
        for log in logs
    ]

    return failed_emails


def collect_failed_registrations(
    since: datetime,
) -> list[FailedRegistration]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event="registration_failure",
    ).order_by("timestamp")

    form_sorted_logs = sorted(logs, key=lambda x: x.content_object.form.admin_name)

    grouped_logs = groupby(form_sorted_logs, key=lambda log: log.content_object.form)

    failed_registrations = []
    for form, submission_logs in grouped_logs:
        logs = list(submission_logs)
        timestamps = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_registrations.append(
            FailedRegistration(
                form_name=form.name,
                failed_submissions_counter=len(logs),
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                admin_link=get_filtered_submission_admin_url(
                    form.id, filter_retry=True, registration_time="24hAgo"
                ),
                has_errors=has_errors,
            )
        )

    return failed_registrations


def collect_failed_prefill_plugins(since: datetime) -> list[FailedPrefill]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event__in=[
            "prefill_retrieve_empty",
            "prefill_retrieve_failure",
        ],
    ).order_by("extra_data__plugin_label")

    grouped_logs = groupby(logs, key=lambda x: x.extra_data["plugin_label"])

    failed_prefill_plugins = []
    for prefill_plugin, submission_logs in grouped_logs:
        logs = list(submission_logs)

        timestamps = []
        forms = set()
        submission_ids = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            forms.add(log.content_object.form.admin_name)
            submission_ids.append(log.object_id)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_prefill_plugins.append(
            FailedPrefill(
                plugin_label=prefill_plugin,
                form_names=sorted(forms),
                submission_ids=submission_ids,
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                has_errors=has_errors,
            )
        )

    return failed_prefill_plugins


def collect_broken_configurations() -> list[BrokenConfiguration]:
    check_brk_configuration = check_brk_config_for_addressNL()

    broken_configurations = []
    if check_brk_configuration:
        broken_configurations.append(
            BrokenConfiguration(
                config_name=_("BRK Client"), exception_message=check_brk_configuration
            )
        )

    return broken_configurations
