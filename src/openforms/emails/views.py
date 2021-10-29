from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from openforms.emails.context import get_wrapper_context
from openforms.submissions.models import Submission


class EmailWrapperTestView(TemplateView):
    template_name = "emails/wrapper.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        content = "<b>content goes here</b>"

        if kwargs.get("submission_id"):
            submission = get_object_or_404(Submission, id=kwargs["submission_id"])
            email_template = submission.form.confirmation_email_template
            content = email_template.render(submission)

        ctx.update(get_wrapper_context(content))
        ctx.update(kwargs)
        return ctx
