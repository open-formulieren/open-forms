from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.views.generic import DetailView, View

from openforms.submissions.models import Submission

from .report import Report


class SubmissionPDFTestView(DetailView):
    """
    Dev-only view to test/implement the PDF styling.

    Note that this should match the method
    ``openforms.submissions.models.SubmissionReport.generate_submission_report_pdf``
    in terms of template name and context used.

    .. todo:: refactor view/method to always use same template/context without
       duplicating code
    """

    template_name = "report/submission_report.html"
    queryset = Submission.objects.all()
    context_object_name = "submission"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG or not request.user.is_superuser:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()

        submission = ctx["submission"]
        ctx["report"] = Report(submission)

        return ctx


class LogFileView(View):
    def get(self, reuest, *args, **kwargs):
        log_file = settings.LOGGING["handlers"]["project"]["filename"]
        return FileResponse(open(log_file, "rb"), content_type="text/plain")
