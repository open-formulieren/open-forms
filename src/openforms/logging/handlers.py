from __future__ import annotations

import logging  # noqa: TID251
from collections.abc import Collection, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from django.db import models

import structlog
from structlog.typing import EventDict
from typing_extensions import TypeIs

from .constants import TimelineLogTags

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from openforms.accounts.models import User
    from openforms.plugins.plugin import AbstractBasePlugin

logger = structlog.stdlib.get_logger(__name__)


@dataclass(slots=True, frozen=True, kw_only=True)
class EventDetails:
    event: str
    """
    Canonical event name of the thing that happened.
    """
    instance: models.Model
    """
    Main database object this log event is about.
    """
    extra_data: Mapping[str, object] | None = None
    """
    Additional data to store in the extra_data JSON field.

    Must be JSON-serializable!
    """
    plugin: AbstractBasePlugin | None = None
    """
    The relevant plugin used, if available.
    """
    error: Exception | None = None
    """
    Any relevant Python exception to include in the log record.
    """
    tags: Collection[TimelineLogTags] = frozenset()
    """
    Tags/markers to query/filter log records on.
    """
    user: User | AnonymousUser | None = None
    """
    The current user that triggerd the log event.
    """

    def get_template_name(self) -> str:
        return f"logging/events/{self.event}.txt"

    def get_user(self) -> User | None:
        from openforms.accounts.models import User

        # If user is not authenticated (eg. AnonymousUser) we can not
        # save it on the TimelineLogProxy model
        if self.user and self.user.is_authenticated:
            assert isinstance(self.user, User)
            return self.user
        return None

    def get_extra_data(self) -> Mapping[str, object]:
        extra_data: dict[str, object] = {}
        if self.extra_data:
            extra_data |= self.extra_data
        if self.plugin:
            extra_data |= {
                "plugin_id": self.plugin.identifier,
                "plugin_label": str(self.plugin.verbose_name),
            }
        if self.error:
            extra_data["error"] = str(self.error)

        for tag in self.tags:
            extra_data[tag] = True

        return extra_data


class Adapter(Protocol):
    def __call__(self, event_dict: EventDict) -> EventDetails | None: ...


def is_event_dict(msg: str | Any) -> TypeIs[EventDict]:
    return isinstance(msg, dict)


@contextmanager
def supress_errors():
    try:
        yield
    except Exception as exc:
        logger.error("log_saving_failed", exc_info=exc)


class TimelineLoggerHandler(logging.Handler):
    """
    Save a log record into a django-timeline-logger record.

    Logs saved to the local database are typically intended to be easily accessible,
    e.g. audit logs, without requiring access to a dedicated log storage like Loki.

    This handler goes hand-in-hand with structlog:

    * it looks at the structlog event to call additional (pre)-processing, allowing
      additional metadata extraction
    * the additional log attributes are stored as structured data
    """

    def __init__(self, *args, adapter: Adapter, **kwargs):
        self.adapter = adapter
        super().__init__(*args, **kwargs)

    @supress_errors()
    def emit(self, record: logging.LogRecord):
        from .models import TimelineLogProxy

        assert is_event_dict(record.msg), "Only structlog event dicts are expected"
        event_details = self.adapter(record.msg)
        if event_details is None:
            return

        # create DB record
        # TODO: validate that the provided template name exists!
        TimelineLogProxy.objects.create(
            content_object=event_details.instance,
            template=event_details.get_template_name(),
            extra_data=event_details.get_extra_data(),
            user=event_details.get_user(),
        )
