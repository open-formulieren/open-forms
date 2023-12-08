from django.views.generic import DetailView

from openforms.config.templatetags.theme import THEME_OVERRIDE_CONTEXT_VAR
from openforms.submissions.models import Submission
from openforms.utils.views import DevViewMixin

from .report import Report


class SubmissionPDFTestView(DevViewMixin, DetailView):
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()

        submission = ctx["submission"]
        ctx["report"] = Report(submission)
        # apply form-specific theme override, if set
        ctx[THEME_OVERRIDE_CONTEXT_VAR] = submission.form.theme

        return ctx
