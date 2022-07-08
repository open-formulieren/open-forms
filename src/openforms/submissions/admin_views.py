from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView

from .models import Submission


class LogsEvaluatedLogicView(PermissionRequiredMixin, LoginRequiredMixin, ListView):

    template_name = "submission_logs/submission_logs.html"
    context_object_name = "logs_activity"
    permission_required = "submissions.view_submission"

    def get_queryset(self):
        self.id = self.kwargs["submission_id"]
        self.submission = Submission.objects.get(id=self.id)
        self.queryset = self.submission.logs.filter(
            template="logging/events/submission_logic_evaluated.txt"
        ).order_by("timestamp")
        return super().get_queryset()

    def get_context_data(self):
        context = super().get_context_data()
        context["opts"] = Submission._meta
        context["original"] = self.submission
        return context
