from copy import copy

from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from openforms.admin.decorators import suppress_requests_errors

from .base import BasePlugin
from .constants import AppointmentDetailsStatus
from .fields import AppointmentBackendChoiceField
from .models import Appointment, AppointmentInfo, AppointmentProduct, AppointmentsConfig
from .registry import register
from .utils import get_plugin


class PluginFieldMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, AppointmentBackendChoiceField):
            field_copy = copy(db_field)
            field_copy.choices = register.get_choices()
            return super().formfield_for_dbfield(field_copy, request, **kwargs)  # type: ignore
        return super().formfield_for_dbfield(db_field, request, **kwargs)  # type: ignore


@suppress_requests_errors(AppointmentsConfig, fields=["limit_to_location"])
@admin.register(AppointmentsConfig)
class AppointmentsConfigAdmin(PluginFieldMixin, SingletonModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "limit_to_location":
            try:
                plugin = get_plugin()
            except ValueError:
                return super().formfield_for_dbfield(
                    db_field,
                    request,
                    disabled=True,
                    widget=AdminTextInputWidget(
                        attrs={"placeholder": _("Please configure the plugin first")}
                    ),
                    **kwargs,
                )

            locations = plugin.get_locations()
            field_copy = copy(db_field)
            field_copy.choices = [
                (location.identifier, location.name) for location in locations
            ]
            return super().formfield_for_dbfield(field_copy, request, **kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)


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
    raw_id_fields = ("submission",)
    search_fields = ("submission__id", "submission__uuid", "appointment_id")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("submission")

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if not request.user.is_superuser:
            list_display.remove("get_object_actions")
        return list_display

    def get_object_actions(self, obj: AppointmentInfo) -> str:
        if not obj.status == AppointmentDetailsStatus.success:
            return "-"

        if obj.start_time and obj.start_time <= timezone.now():
            return "-"

        link = BasePlugin.get_cancel_link(obj.submission)
        return format_html('<a href="{}">{}</a>', link, _("Cancel"))

    get_object_actions.short_description = _("Appointment actions")


class AppointmentProductInline(admin.TabularInline):
    model = AppointmentProduct
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(PluginFieldMixin, admin.ModelAdmin):
    list_display = ("submission", "location", "datetime", "plugin")
    list_filter = ("plugin", "datetime")
    list_select_related = ("submission",)
    search_fields = ("submission__uuid",)
    date_hierarchy = "datetime"
    ordering = ("-datetime", "-pk")
    raw_id_fields = ("submission",)
    inlines = [AppointmentProductInline]
