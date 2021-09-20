from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from timeline_logger.models import TimelineLog

from openforms.submissions.models import Submission


class TimelineLogProxyQueryset(models.QuerySet):
    def filter_event(self, event: str):
        return self.filter(extra_data__log_event=event)


class TimelineLogProxy(TimelineLog):
    class Meta:
        proxy = True
        verbose_name = _("timeline log entry")
        verbose_name_plural = _("timeline log entries")

    objects = TimelineLogProxyQueryset.as_manager()

    @property
    def fmt_lead(self):
        if self.is_submission:
            return f"[{self.fmt_time}] ({self.fmt_sub})"
        elif self.content_type_id:
            return (
                f"[{self.fmt_time}] ({self.content_type.name} {self.content_object.id})"
            )
        else:
            return f"[{self.fmt_time}]"

    @property
    def fmt_time(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def fmt_sub(self):
        if not self.is_submission:
            return ""
        return f"Submission {self.content_object.id}"

    @property
    def fmt_user(self):
        if self.user_id:
            return '{} "{}"'.format(gettext("User"), str(self.user))
        return gettext("Anonymous user")

    @property
    def fmt_form(self):
        if not self.is_submission:
            return ""
        return f'"{self.content_object.form}" (ID: {self.content_object.form_id})'

    @property
    def is_submission(self):
        return bool(self.content_type == ContentType.objects.get_for_model(Submission))

    @property
    def fmt_plugin(self):
        if not self.extra_data:
            return _("(unknown)")
        plugin_id = self.extra_data.get("plugin_id", "")
        plugin_label = self.extra_data.get("plugin_label", "")
        return f'"{plugin_label}" ({plugin_id})'

    def content_admin_url(self):
        if self.object_id and self.content_type_id:
            ct = self.content_type
            return reverse(
                f"admin:{ct.app_label}_{ct.model}_change", args=(self.object_id,)
            )
        else:
            return ""

    def content_admin_link(self):
        url = self.content_admin_url()
        if url:
            return format_html(
                '<a href="{u}">{t}</a>', u=url, t=str(self.content_object)
            )
        else:
            return ""

    content_admin_link.short_description = _("content object")

    def message(self):
        return self.get_message()

    message.short_description = _("message")
