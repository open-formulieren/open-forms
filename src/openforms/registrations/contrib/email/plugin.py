import html
from mimetypes import types_map
from typing import NoReturn

from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from openforms.emails.utils import send_mail_html, strip_tags_plus
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.submissions.tasks.registration import set_submission_reference

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
        submitted_data = submission.get_printable_data()

        # explicitly get a reference before registering
        set_submission_reference(submission)

        subject = _("[Open Forms] {form_name} - submission {public_reference}").format(
            form_name=submission.form.admin_name,
            public_reference=submission.public_registration_reference,
        )

        context = {
            "form_name": submission.form.admin_name,
            "public_reference": submission.public_registration_reference,
            "datetime": timezone.localtime(submission.completed_on).strftime(
                "%H:%M:%S %d-%m-%Y"
            ),
            "submitted_data": submitted_data,
        }

        html_template = get_template("emails/email_registration.html")
        text_template = get_template("emails/email_registration.txt")

        html_content = html_template.render(context)
        context["rendering_text"] = True
        text_content = text_template.render(context)

        # post process since the mail template has html markup and django escaped entities
        text_content = strip_tags_plus(text_content)
        text_content = html.unescape(text_content)

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
                    f"{submission.form.admin_name} - submission.{attachment_format}",
                    export_data,
                    mime_type,
                )
                extra_attachments.append(attachment)
            elif attachment_format == AttachmentFormat.pdf:
                attachment = (
                    submission.report.title,
                    submission.report.content.read(),
                    mime_type,
                )
                extra_attachments.append(attachment)

        send_mail_html(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            options["to_emails"],
            fail_silently=False,
            attachment_tuples=attachments + extra_attachments,
            text_message=text_content,
        )

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Email plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission", options: dict):
        subject = _(
            "[Open Forms] {form_name} - submission payment received {public_reference}"
        ).format(
            form_name=submission.form.admin_name,
            public_reference=submission.public_registration_reference,
        )
        message = _(
            "Submission payment received for {form_name} (submitted on {datetime})"
        ).format(
            form_name=submission.form.admin_name,
            datetime=submission.completed_on.strftime("%H:%M:%S %d-%m-%Y"),
        )

        html_message = format_html("<p>{}</p>", message)

        send_mail_html(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            options["to_emails"],
            fail_silently=False,
        )
