"""
Custom structlog processors.
"""

from django.conf import settings

from structlog.typing import EventDict, WrappedLogger


def drop_user_agent_in_dev(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
):
    if settings.DEBUG and "user_agent" in event_dict:
        del event_dict["user_agent"]
    return event_dict


def add_timeline_logger_attributes(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    Enrich the event dict with django-timeline-logger model context.

    This additional context is only relevant for snapshotting in timeline-logger and not
    for outputting to the console.
    """
    # only process audit events - this is the marker for records that get stored in
    # the DB
    if not (event_dict.get("audit", False)):
        return event_dict

    # Set the extra data as custom attribute rather than a key in the event dict, so
    # that it doesn't get output by regular structlog formatters
    event_dict._timeline_logger_data = {  # pyright: ignore[reportAttributeAccessIssue]
        "event": event_dict,
    }

    match event_dict["event"]:
        case "hijack_started":
            pass

    return event_dict
