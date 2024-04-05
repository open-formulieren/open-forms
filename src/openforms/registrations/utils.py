from datetime import datetime
from typing import Any, Callable

from glom import assign, glom

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models import Submission
from openforms.submissions.utils import get_filtered_submission_admin_url

unset = object()


def execute_unless_result_exists(
    callback: Callable,
    submission: Submission,
    spec: str,
    default=None,
    result=unset,
) -> Any:
    if submission.registration_result is None:
        submission.registration_result = {}

    existing_result = glom(submission.registration_result, spec, default=default)
    if existing_result:
        return existing_result

    callback_result = callback()

    if result is unset:
        result = callback_result

    # store the result
    assign(submission.registration_result, spec, result, missing=dict)
    submission.save(update_fields=["registration_result"])
    return callback_result


def collect_registrations_failures(since: datetime) -> list[dict[str, str] | None]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event="registration_failure",
        extra_data__include_in_daily_digest=True,
    ).order_by("timestamp")

    if not logs:
        return

    connected_forms = {}
    for log in logs:
        form = log.content_object.form

        if form.uuid in connected_forms:
            connected_forms[form.uuid]["failed_submissions_counter"] += 1
            connected_forms[form.uuid]["last_failure_at"] = log.timestamp
        else:
            connected_forms[form.uuid] = {
                "form_name": form.name,
                "failed_submissions_counter": 1,
                "initial_failure_at": log.timestamp,
                "last_failure_at": log.timestamp,
                "admin_link": get_filtered_submission_admin_url(form.id, 1, "24hAgo"),
            }

    failed_registrations = [form_detail for form_detail in connected_forms.values()]

    return failed_registrations
