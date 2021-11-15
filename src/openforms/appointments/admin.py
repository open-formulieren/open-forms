from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .constants import AppointmentDetailsStatus
from .models import AppointmentInfo, AppointmentsConfig
from .tokens import submission_appointment_token_generator


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
        "get_cancel_link",
        "get_change_link",
    )
    list_filter = ("status", "start_time")
    date_hierarchy = "created"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("submission")

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            list_display.remove("get_cancel_link")
            list_display.remove("get_change_link")
        return list_display

    def get_cancel_link(self, obj) -> str:
        if not obj.status == AppointmentDetailsStatus.success:
            return ""

        token = submission_appointment_token_generator.make_token(obj.submission)
        url = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "submission_uuid": obj.submission.uuid,
                "token": token,
            },
        )
        return format_html(
            '<a href="{url}">{text}</a>',
            url=url,
            text=_("Cancel appointment"),
        )

    get_cancel_link.short_description = _("Cancel link")

    def get_change_link(self, obj) -> str:
        if not obj.status == AppointmentDetailsStatus.success:
            return ""

        token = submission_appointment_token_generator.make_token(obj.submission)
        url = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "submission_uuid": obj.submission.uuid,
                "token": token,
            },
        )
        return format_html(
            '<a href="{url}">{text}</a>',
            url=url,
            text=_("Change appointment"),
        )

    get_change_link.short_description = _("Change link")
