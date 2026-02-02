"""
Adapt structlog log records to django-timeline-logger compatible properties.
"""

from structlog.typing import EventDict

from .constants import TimelineLogTags
from .handlers import EventDetails


def from_structlog(event_dict: EventDict) -> EventDetails | None:
    """
    Transform structlog events into django-timeline-logger parameters.
    """
    from log_outgoing_requests.models import OutgoingRequestsLog

    from openforms.accounts.models import User
    from openforms.analytics_tools.models import AnalyticsToolsConfiguration
    from openforms.submissions.models import Submission, SubmissionStep

    assert "event" in event_dict

    match event_dict:
        #
        # Accounts
        #
        case {
            "event": "hijack_started" | "hijack_ended" as event,
            "hijacked": str(hijacked_username),
            "hijacker": str(hijacker_username),
        }:
            users: dict[str, User] = User.objects.filter(
                username__in=(hijacked_username, hijacker_username)
            ).in_bulk(field_name="username")
            hijacked_user = users[hijacked_username]
            hijacker = users[hijacker_username]
            extra_data = {
                "hijacker": {
                    "id": hijacker.pk,
                    "full_name": hijacker.get_full_name(),
                    "username": hijacker.username,
                },
                "hijacked": {
                    "id": hijacked_user.pk,
                    "full_name": hijacked_user.get_full_name(),
                    "username": hijacked_user.username,
                },
            }
            return EventDetails(
                event=event,
                instance=hijacked_user,
                user=hijacker,
                tags=[TimelineLogTags.hijack],
                extra_data=extra_data,
            )

        #
        # Outgoing requests logs
        #
        case {
            "event": "outgoing_request_log_details_view_admin" as event,
            "object_id": str(object_id),
            "user": str(username),
        }:
            user = User.objects.get(username=username)
            outgoing_request_log = OutgoingRequestsLog.objects.get(pk=object_id)
            return EventDetails(
                event=event,
                instance=outgoing_request_log,
                user=user,
                tags=[TimelineLogTags.AVG],
            )

        #
        # Analytics
        #
        case {
            "event": "analytics_tool_enabled" | "analytics_tool_disabled" as event,
            "analytics_tool": str(tool),
        }:
            config = AnalyticsToolsConfiguration.get_solo()
            return EventDetails(
                event=event,
                instance=config,
                extra_data={"analytics_tool": tool},
            )

        #
        # Submissions
        #
        case {
            "event": "submission_start" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "authentication.submission_auth",
            "submission_uuid": str(submission_uuid),
            "is_delegated": bool(is_delegated),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            user = (
                User.objects.get(username=username)
                if (username := event_dict.get("username"))
                else None
            )
            return EventDetails(
                event="submission_auth",
                instance=submission,
                user=user,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={"delegated": is_delegated},
            )

        case {
            "event": "submission_step_fill" as event,
            "step_id": int(step_pk),
        }:
            step = SubmissionStep.objects.select_related(
                "submission", "form_step__form_definition"
            ).get(pk=step_pk)
            assert step.form_step is not None
            return EventDetails(
                event=event,
                instance=step.submission,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={
                    "step": str(step.form_step.form_definition.name),
                    "step_id": step_pk,
                },
            )

    return None
