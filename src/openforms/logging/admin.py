from django.contrib import admin
from django.http import HttpRequest

from import_export import resources
from import_export.admin import ExportActionModelAdmin
from import_export.fields import Field
from timeline_logger.models import TimelineLog

from openforms.logging.models import AVGTimelineLogProxy, TimelineLogProxy


class TimelineLogProxyResource(resources.ModelResource):
    user = Field(attribute="user")
    related_object = Field(attribute="content_object")
    message = Field(attribute="message")
    event = Field(attribute="extra_data")

    class Meta:
        model = TimelineLogProxy
        fields = ("user", "related_object", "message", "timestamp")

    def dehydrate_user(self, obj: TimelineLogProxy) -> str:
        return obj.fmt_user

    def dehydrate_related_object(self, obj: TimelineLogProxy) -> str | None:
        if obj.content_object is None:
            return None

        return str(obj.content_object)

    def dehydrate_message(self, obj: TimelineLogProxy) -> str:
        return obj.message().strip()

    def dehydrate_timestamp(self, obj: TimelineLogProxy) -> str:
        return obj.timestamp.isoformat()

    def dehydrate_event(self, obj: TimelineLogProxy) -> str | None:
        if not obj.extra_data:
            return None
        return obj.extra_data.get("log_event")


@admin.register(TimelineLogProxy)
class TimelineLogProxyAdmin(ExportActionModelAdmin):
    fields = (
        "message",
        "timestamp",
        "content_admin_link",
        "user",
        "extra_data",
    )
    list_display = ("message",)
    list_filter = ("timestamp", "user")
    search_fields = (
        "extra_data",
        "object_id",
    )
    date_hierarchy = "timestamp"

    # Export options:
    resource_classes = [TimelineLogProxyResource]

    def has_add_permission(self, request: HttpRequest):
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: TimelineLogProxy | None = None
    ):
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: TimelineLogProxy | None = None
    ):
        return False


@admin.register(AVGTimelineLogProxy)
class AVGTimelineLogProxyAdmin(TimelineLogProxyAdmin):
    pass


admin.site.unregister(TimelineLog)
