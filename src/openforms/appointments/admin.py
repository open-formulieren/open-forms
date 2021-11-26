from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .base import BasePlugin
from .constants import AppointmentDetailsStatus
from .models import AppointmentInfo, AppointmentsConfig


@admin.register(AppointmentsConfig)
class AppointmentsConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(AppointmentInfo)
class AppointmentInfoAdmin(admin.ModelAdmin):
    list_display = (
        "status",
        "appointment_id",
        "start_time",
        "submission",
        "get_object_actions",
    )
    list_filter = ("status", "start_time")
    date_hierarchy = "created"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("submission")

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            list_display.remove("get_object_actions")
        return list_display

    def get_object_actions(self, obj) -> str:
        if not obj.status == AppointmentDetailsStatus.success:
            return "-"

        if obj.start_time and obj.start_time <= timezone.now():
            return "-"

        actions = [
            ("change", _("Change")),
            ("cancel", _("Cancel")),
        ]
        links = (
            (BasePlugin.get_link(obj.submission, verb=action), label)
            for action, label in actions
        )
        return format_html_join(" | ", '<a href="{}">{}</a>', links)

    get_object_actions.short_description = _("Appointment actions")
