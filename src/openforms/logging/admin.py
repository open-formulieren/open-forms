from django.contrib import admin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path

from timeline_logger.models import TimelineLog
from timeline_logger.views import TimelineLogListView

from openforms.logging.models import AvgTimelineLogProxy, TimelineLogProxy


class TimelineLogView(PermissionRequiredMixin, TimelineLogListView):
    queryset = TimelineLogProxy.objects.order_by("-timestamp")
    template_name = "logging/admin_list.html"
    permission_required = "logging.view_timelinelogproxy"


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

    def get_urls(self):
        urls = super().get_urls()
        audit_log_list_view = self.admin_site.admin_view(TimelineLogView.as_view())
        custom = [
            path("auditlog/", audit_log_list_view, name="audit-log"),
        ]
        return custom + urls

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AvgTimelineLogProxy)
class AvgTimelineLogProxyAdmin(TimelineLogProxyAdmin):
    pass


admin.site.unregister(TimelineLog)
