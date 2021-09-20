from timeline_logger.views import TimelineLogListView

from openforms.logging.models import TimelineLogProxy


class TimelineLogView(TimelineLogListView):
    queryset = TimelineLogProxy.objects.order_by("-timestamp")
    template_name = "logging/admin_list.html"
