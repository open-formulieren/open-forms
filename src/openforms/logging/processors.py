"""
Custom structlog processors.
"""

import logging  # noqa: TID251

from django.conf import settings

from maykin_common.config import config
from structlog.stdlib import filter_by_level
from structlog.typing import EventDict, WrappedLogger


def drop_user_agent_in_dev(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
):
    if settings.DEBUG and "user_agent" in event_dict:
        del event_dict["user_agent"]
    return event_dict


def filter_by_level_or_audit(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Always let through ``audit`` events, irrespective of the level.
    """
    if event_dict.get("audit") is True:
        if method_name == "debug" and config(
            "DEBUG", default=False
        ):  # pragma: no cover
            raise Exception(
                "Audit log records with level 'debug' do not get emitted. Use 'info' "
                "or higher."
            )
        return event_dict
    return filter_by_level(logger, method_name=method_name, event_dict=event_dict)
