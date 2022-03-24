from typing import List

from django.db import models
from django.template.defaultfilters import capfirst
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from timeline_logger.models import TimelineLog

from openforms.forms.models import Form
from openforms.logging.constants import TimelineLogTags
from openforms.submissions.models import Submission


class TimelineLogProxyQueryset(models.QuerySet):
    def filter_event(self, event: str):
        return self.filter(extra_data__log_event=event)

    def has_tag(self, tag: str):
        return self.filter(extra_data__contains={tag: True})

    def exclude_tag(self, tag: str):
        return self.exclude(extra_data__contains={tag: True})


class TimelineLogProxy(TimelineLog):
    objects = TimelineLogProxyQueryset.as_manager()

    class Meta:
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
        if not self.is_submission:
            return ""
        prefix = capfirst(Submission._meta.verbose_name)
        return f"{prefix} {self.object_id}"

    @property
    def fmt_user(self) -> str:
        # if there is a .user they own the log line (usually AVG type logs)
        if self.user_id:
            return _("Staff user {user}").format(user=str(self.user))
        if self.is_submission:
            auth = self.content_object.get_auth_mode_display()
            if auth:
                return _("Authenticated via plugin {auth}").format(auth=auth)
        else:
            return gettext("Anonymous user")

    @property
    def fmt_form(self) -> str:
        if self.is_submission:
            return f'"{self.content_object.form}" (ID: {self.content_object.form_id})'
        elif self.is_form:
            return f'"{self.content_object}" (ID: {self.object_id})'
        return ""

    @property
    def is_submission(self) -> bool:
        return isinstance(self.content_object, Submission)

    @property
    def is_form(self) -> bool:
        return isinstance(self.content_object, Form)

    @property
    def fmt_plugin(self) -> str:
        if not self.extra_data:
            return _("(unknown)")
        plugin_id = self.extra_data.get("plugin_id", "")
        plugin_label = self.extra_data.get("plugin_label", "")
        if not any([plugin_id, plugin_label]):
            return ""
        return f'"{plugin_label}" ({plugin_id})'

    def get_formatted_prefill_fields(self, fields) -> List:
        formatted_fields = []
        components = self.content_object.form.iter_components(recursive=True)

        for component in components:
            for field in fields:
                try:
                    if component["prefill"]["attribute"] == field:
                        formatted_fields.append(f"{component['label']} ({field})")
                except KeyError:
                    pass

        return formatted_fields

    @property
    def fmt_prefill_fields(self) -> str:
        if not self.extra_data or "prefill_fields" not in self.extra_data:
            return _("(unknown)")
        formatted_fields = self.get_formatted_prefill_fields(
            self.extra_data["prefill_fields"]
        )
        return ", ".join(formatted_fields)

    @property
    def fmt_url(self) -> str:
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
            return self.content_object.registration_attempts
        else:
            return ""

    def content_admin_link(self) -> str:
        if not (url := self.content_admin_url):
            return ""

        return format_html('<a href="{u}">{t}</a>', u=url, t=str(self.content_object))

    content_admin_link.short_description = _("content object")

    def message(self) -> str:
        return self.get_message()

    message.short_description = _("message")

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
    objects = AVGTimelineLogProxyManager()

    class Meta:
        proxy = True
        verbose_name = _("avg timeline log entry")
        verbose_name_plural = _("avg timeline log entries")
