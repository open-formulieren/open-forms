from django.contrib import admin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path

from timeline_logger.models import TimelineLog
from timeline_logger.views import TimelineLogListView

from openforms.logging.models import AVGTimelineLogProxy, TimelineLogProxy


@admin.register(TimelineLogProxy)
class TimelineLogProxyAdmin(admin.ModelAdmin):
    fields = (
        "message",
        "timestamp",
        "content_admin_link",
        "user",
        "extra_data",
    )
    list_display = ("message",)
    search_fields = (
        "extra_data",
        "object_id",
    )
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AVGTimelineLogProxy)
class AVGTimelineLogProxyAdmin(TimelineLogProxyAdmin):
    pass


admin.site.unregister(TimelineLog)
