from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from openforms.submissions.models import Submission

from .confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
    render_confirmation_email_template,
)
from .context import get_wrapper_context
from .utils import strip_tags_plus


class EmailWrapperTestView(TemplateView):
    template_name = "emails/wrapper.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG or not request.user.is_superuser:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def _get_mode(self) -> str:
        mode = self.request.GET.get("mode", "html")
        assert mode in ("html", "text"), f"Unknown mode: {mode}"
        return mode

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        content = "<b>content goes here</b>"

        if kwargs.get("submission_id"):
            submission = get_object_or_404(Submission, id=kwargs["submission_id"])

            content_template = get_confirmation_email_templates(submission)[1]
            context = get_confirmation_email_context_data(submission)
            mode = self._get_mode()
            if mode == "text":
                context["rendering_text"] = True
            content = render_confirmation_email_template(content_template, context)
            if mode == "text":
                content = strip_tags_plus(content, keep_leading_whitespace=True)

        ctx.update(get_wrapper_context(content))
        ctx.update(kwargs)
        return ctx

    def render_to_response(self, context, **response_kwargs):
        mode = self._get_mode()
        if mode == "text":
            return HttpResponse(
                context["content"].encode("utf-8"), content_type="text/plain"
            )
        return super().render_to_response(context, **response_kwargs)
