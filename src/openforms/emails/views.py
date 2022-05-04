from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from openforms.submissions.models import Submission
from openforms.utils.views import DevViewMixin, EmailDebugViewMixin

from .confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
    render_confirmation_email_template,
)
from .utils import strip_tags_plus


class EmailWrapperTestView(
    DevViewMixin, EmailDebugViewMixin, TemplateView
):  # pragma: nocover
    def get_email_content(self):
        content = "<b>content goes here</b>"

        if self.kwargs.get("submission_id"):
            submission = get_object_or_404(Submission, id=self.kwargs["submission_id"])

            content_template = get_confirmation_email_templates(submission)[1]
            context = get_confirmation_email_context_data(submission)
            mode = self._get_mode()
            if mode == "text":
                context["rendering_text"] = True
            content = render_confirmation_email_template(content_template, context)
            if mode == "text":
                content = strip_tags_plus(content, keep_leading_whitespace=True)

        return content
