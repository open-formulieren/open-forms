from mimetypes import types_map
from typing import NoReturn

from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from openforms.emails.utils import sanitize_content
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.utils.email import send_mail_plus

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference
from ...registry import register
from .config import EmailOptionsSerializer
from .constants import AttachmentFormat


@register("email")
class EmailRegistration(BasePlugin):
    verbose_name = _("Email registration")
    configuration_options = EmailOptionsSerializer

    def register_submission(self, submission: Submission, options: dict) -> None:
        submitted_data = submission.get_merged_data()

        template = _("Submission details for {} (submitted on {})").format(
            submission.form.admin_name,
            submission.completed_on.strftime("%H:%M:%S %d-%m-%Y"),
        )

        template += """
            {% for field, value in submitted_data.items %}
                {{field}}: {% display_value value %}
            {% endfor %}
        """

        # render the e-mail body - the template from this model.
        rendered_content = Template(template).render(
            Context({"submitted_data": submitted_data})
        )
        sanitized = sanitize_content(rendered_content)

        default_template = get_template("confirmation_mail.html")
        content = default_template.render({"body": mark_safe(sanitized)})

        attachments = submission.attachments.as_mail_tuples()

        attachment_formats = options.get("attachment_formats", [])
        extra_attachments = []
        for attachment_format in attachment_formats:
            mime_type = types_map[f".{attachment_format}"]
            if attachment_format in [AttachmentFormat.csv, AttachmentFormat.xlsx]:
                export_data = create_submission_export(
                    Submission.objects.filter(pk=submission.pk)
                ).export(attachment_format)

                attachment = (
                    f"{submission.form.name} - submission.{attachment_format}",
                    export_data,
                    mime_type,
                )
            elif attachment_format == AttachmentFormat.pdf:
                attachment = (
                    submission.report.title,
                    submission.report.content.read(),
                    mime_type,
                )

            extra_attachments.append(attachment)

        send_mail_plus(
            _("[Open Forms] {} - submission {}").format(
                submission.form.admin_name, submission.uuid
            ),
            content,
            settings.DEFAULT_FROM_EMAIL,
            options["to_emails"],
            fail_silently=False,
            html_message=content,
            attachments=attachments + extra_attachments,
        )

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Email plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission"):
        pass
