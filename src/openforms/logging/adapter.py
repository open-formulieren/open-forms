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
    from openforms.accounts.models import User

    assert "event" in event_dict

    match event_dict:
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

    return None
