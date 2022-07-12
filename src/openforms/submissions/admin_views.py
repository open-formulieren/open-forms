from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from openforms.utils.mixins import UserIsStaffMixin

from .models import Submission


class LogsEvaluatedLogicView(UserIsStaffMixin, PermissionRequiredMixin, ListView):

    template_name = "submission_logs/submission_logs.html"
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
        queryset = self.submission.logs.filter(template=logic_log_template)
        return queryset.order_by("timestamp")

    def get_context_data(self):
        context = super().get_context_data()
        context.update({"opts": Submission._meta, "original": self._submission})
        return context
