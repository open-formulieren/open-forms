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
