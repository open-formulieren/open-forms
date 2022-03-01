from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from openforms.emails.confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
    render_confirmation_email_template,
)
from openforms.emails.context import get_wrapper_context
from openforms.submissions.models import Submission


class EmailWrapperTestView(TemplateView):
    template_name = "emails/wrapper.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG or not request.user.is_superuser:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        content = "<b>content goes here</b>"

        if kwargs.get("submission_id"):
            submission = get_object_or_404(Submission, id=kwargs["submission_id"])

            content_template = get_confirmation_email_templates(submission)[1]
            context = get_confirmation_email_context_data(submission)
            content = render_confirmation_email_template(content_template, context)

        ctx.update(get_wrapper_context(content))
        ctx.update(kwargs)
        return ctx
