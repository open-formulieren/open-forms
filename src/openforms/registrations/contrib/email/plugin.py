from typing import NoReturn

from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from openforms.emails.utils import sanitize_content
from openforms.submissions.models import Submission
from openforms.utils.email import send_mail_plus

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference
from ...registry import register
from .config import EmailOptionsSerializer


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

        send_mail_plus(
            _("[Open Forms] {} - submission {}").format(
                submission.form.admin_name, submission.uuid
            ),
            content,
            settings.DEFAULT_FROM_EMAIL,
            options["to_emails"],
            fail_silently=False,
            html_message=content,
            attachments=attachments,
        )

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Email plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission"):
        pass

    def test_config():
        test = []

        test.append({'completed': False, 'error': 'geen fout melding', 'msg': 'Iets ging fout', 'name': 'name'})
        
        return test
