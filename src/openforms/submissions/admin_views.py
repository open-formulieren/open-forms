from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import ListView

from openforms.logging.models import TimelineLogProxy
from openforms.utils.mixins import UserIsStaffMixin

from .models import Submission


class LogsEvaluatedLogicView(UserIsStaffMixin, PermissionRequiredMixin, ListView):

    template_name = "admin/submissions/submission/logs.html"
    context_object_name = "logs_activity"
    permission_required = "submissions.view_submission"

    @property
    def submission(self):
        if not hasattr(self, "_submission"):
            self._submission = get_object_or_404(
                Submission, id=self.kwargs["submission_id"]
            )
        return self._submission

    def get_queryset(self):
        logic_log_template = "logging/events/submission_logic_evaluated.txt"
        queryset = TimelineLogProxy.objects.filter(
            template=logic_log_template,
            object_id=self.submission.id,
            content_type=ContentType.objects.get_for_model(Submission),
        )
        return queryset.order_by("timestamp")

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "opts": Submission._meta,
                "original": self._submission,
                "title": _("submission logs"),
            }
        )
        return context
