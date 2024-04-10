from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from openforms.emails.tasks import Digest
from openforms.submissions.models import Submission
from openforms.utils.views import DevViewMixin, EmailDebugViewMixin

from .confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
)
from .utils import render_email_template, strip_tags_plus


class EmailWrapperTestView(
    DevViewMixin, EmailDebugViewMixin, TemplateView
):  # pragma: nocover
    def get_email_content(self):
        content = "<b>content goes here</b>"

        match self.kwargs:
            case {"submission_id": int()}:
                submission = get_object_or_404(
                    Submission, id=self.kwargs["submission_id"]
                )

                content_template = get_confirmation_email_templates(submission)[1]
                context = get_confirmation_email_context_data(submission)
                mode = self._get_mode()
                if mode == "text":
                    context["rendering_text"] = True
                content = render_email_template(content_template, context)
                if mode == "text":
                    content = strip_tags_plus(content, keep_leading_whitespace=True)

            case {"email_digest": True}:
                days_before = int(self.request.GET.get("days_before", 1))
                interval = timezone.now() - timedelta(days=days_before)
                digest = Digest(since=interval)
                return digest.render()

            case _:
                pass  # render wrapper

        return content
