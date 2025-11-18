from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, ClassVar

from django.contrib import admin
from django.db import models
from django.template.defaultfilters import capfirst
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from timeline_logger.manager import TimelineLogManager
from timeline_logger.models import TimelineLog

from openforms.formio.typing import Component
from openforms.typing import StrOrPromise

from .constants import TimelineLogTags


class TimelineLogProxyQueryset(models.QuerySet["TimelineLogProxy"]):
    def filter_event(self, event: str):
        return self.filter(extra_data__log_event=event)

    def has_tag(self, tag: str):
        return self.filter(extra_data__contains={tag: True})

    def exclude_tag(self, tag: str):
        return self.exclude(extra_data__contains={tag: True})


class TimelineLogProxyManager(
    TimelineLogManager.from_queryset(TimelineLogProxyQueryset)
):
    if TYPE_CHECKING:

        def for_object(self, obj: models.Model) -> TimelineLogProxyQueryset: ...
        def filter_event(self, event: str) -> TimelineLogProxyQueryset: ...
        def has_tag(self, tag: str) -> TimelineLogProxyQueryset: ...
        def exclude_tag(self, tag: str) -> TimelineLogProxyQueryset: ...


class TimelineLogProxy(TimelineLog):
    content_type_id: int
    user_id: int | None

    objects: ClassVar[TimelineLogProxyManager] = TimelineLogProxyManager()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        proxy = True
        verbose_name = _("timeline log entry")
        verbose_name_plural = _("timeline log entries")

    @property
    def fmt_lead(self) -> str:
        if self.is_submission:
            return f"[{self.fmt_time}] ({self.fmt_sub})"
        elif self.content_type_id and self.object_id:
            return f"[{self.fmt_time}] ({self.content_type.name} {self.object_id})"
        else:
            return f"[{self.fmt_time}]"

    @property
    def fmt_time(self) -> str:
        local_timestamp = timezone.localtime(self.timestamp)
        return local_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")

    @property
    def fmt_sub(self) -> str:
        from openforms.submissions.models import Submission

        if not self.is_submission:
            return ""
        prefix = capfirst(str(Submission._meta.verbose_name))
        return f"{prefix} {self.object_id}"

    @property
    def fmt_user(self) -> str:
        # if there is a .user they own the log line (usually AVG type logs)
        if self.user_id:
            return _("Staff user {user}").format(user=str(self.user))
        if self.is_submission:
            assert self.content_object is not None
            auth = self.content_object.get_auth_mode_display()
            if auth:
                return _("Authenticated via plugin {auth}").format(auth=auth)
        return gettext("Anonymous user")

    @property
    def fmt_form(self) -> str:
        if self.is_submission:
            assert self.content_object is not None
            return f'"{self.content_object.form}" (ID: {self.content_object.form_id})'
        elif self.is_form:
            assert self.content_object is not None
            return f'"{self.content_object}" (ID: {self.object_id})'
        return ""

    @property
    def is_submission(self) -> bool:
        from openforms.submissions.models import Submission

        return isinstance(self.content_object, Submission)

    @property
    def is_form(self) -> bool:
        from openforms.forms.models import Form

        return isinstance(self.content_object, Form)

    @property
    def fmt_plugin(self) -> StrOrPromise:
        if not self.extra_data:
            return _("(unknown)")
        plugin_id = self.extra_data.get("plugin_id", "")
        plugin_label = self.extra_data.get("plugin_label", "")
        if not any([plugin_id, plugin_label]):
            return ""
        return f'"{plugin_label}" ({plugin_id})'

    def get_formatted_prefill_fields(
        self,
        fields: Sequence[str],
    ) -> list[str]:
        formatted_fields: list[str] = []
        assert self.content_object is not None
        components: Iterator[Component] = self.content_object.form.iter_components(
            recursive=True
        )

        for component in components:
            for field in fields:
                if (
                    "prefill" not in component
                    or "attribute" not in component["prefill"]
                ):
                    continue
                if component["prefill"]["attribute"] == field:
                    formatted_fields.append(f"{component['label']} ({field})")

        return formatted_fields

    @property
    def fmt_prefill_fields(self) -> StrOrPromise:
        if (
            not self.extra_data
            or "prefill_fields" not in self.extra_data
            or not self.content_object
        ):
            return _("(unknown)")
        formatted_fields = self.get_formatted_prefill_fields(
            self.extra_data["prefill_fields"]
        )
        return ", ".join(formatted_fields)

    @property
    def fmt_url(self) -> StrOrPromise:
        if not self.extra_data or "url" not in self.extra_data:
            return _("(unknown)")
        return self.extra_data["url"]

    @property
    def content_admin_url(self) -> str:
        if not (self.object_id and self.content_type_id):
            return ""

        ct = self.content_type
        return reverse(
            f"admin:{ct.app_label}_{ct.model}_change", args=(self.object_id,)
        )

    @property
    def fmt_submission_registration_attempts(self):
        if self.is_submission:
            assert self.content_object is not None
            return self.content_object.registration_attempts
        else:
            return ""

    @admin.display(description=_("content object"))
    def content_admin_link(self) -> str:
        if not (url := self.content_admin_url):
            return ""

        return format_html('<a href="{u}">{t}</a>', u=url, t=str(self.content_object))

    @admin.display(description=_("message"))
    def message(self) -> str:
        return self.get_message()

    @property
    def event(self):
        if not self.extra_data:
            return None
        else:
            return self.extra_data.get("log_event", None)


class AVGTimelineLogProxyManager(models.Manager):
    def get_queryset(self):
        return TimelineLogProxyQueryset(self.model, using=self._db).has_tag(
            TimelineLogTags.AVG
        )


class AVGTimelineLogProxy(TimelineLogProxy):
    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        AVGTimelineLogProxyManager
    ] = AVGTimelineLogProxyManager()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        proxy = True
        verbose_name = _("avg timeline log entry")
        verbose_name_plural = _("avg timeline log entries")
