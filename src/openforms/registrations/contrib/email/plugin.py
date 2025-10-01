import html
from mimetypes import types_map
from typing import Any

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language_info, gettext_lazy as _

import structlog

from openforms.config.data import Action
from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from openforms.emails.utils import (
    render_email_template,
    send_mail_html,
    strip_tags_plus,
)
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.submissions.rendering.constants import RenderModes
from openforms.submissions.rendering.renderer import Renderer
from openforms.template import render_from_string
from openforms.variables.utils import get_variables_for_context

from ...base import BasePlugin
from ...registry import register
from .checks import check_config
from .config import EmailOptionsSerializer, Options
from .constants import PLUGIN_ID, AttachmentFormat
from .models import EmailConfig
from .utils import get_registration_email_templates

logger = structlog.stdlib.get_logger(__name__)


@register(PLUGIN_ID)
class EmailRegistration(BasePlugin[Options]):
    verbose_name = _("Email registration")
    configuration_options = EmailOptionsSerializer

    def verify_initial_data_ownership(
        self, submission: Submission, options: Options
    ) -> None:
        """
        Ownership checks for email registration are not meaningful, allow anything.
        """
        pass

    @staticmethod
    def get_recipients(submission: Submission, options: Options) -> list[str]:
        log = logger.bind(
            submission_uuid=str(submission.uuid), form_uuid=str(submission.form.uuid)
        )
        state = submission.load_submission_value_variables_state()
        # ensure we have a fallback
        recipients: list[str] = options["to_emails"]

        # TODO: validate in the options that this key/variable exists, but we can't
        # do that because variables get created *after* the registration options are
        # submitted...
        if variable_key := options.get("to_emails_from_variable"):
            log = log.bind(variable=variable_key)
            log.info("lookup_recipient_from_variable")
            try:
                variable = state.get_variable(variable_key)
            except KeyError:
                log.info("variable_not_found")
            else:
                log.info("variable_found")
                if variable_value := variable.value:
                    # Normalize to a list of email addresses. Note that a form component
                    # could be used with multiple=True, then it will already be a list of
                    # values.
                    if not isinstance(variable_value, list):
                        variable_value = [variable_value]

                    # do not validate that the values are emails, if they're wrong values,
                    # we want to see this in error monitoring.
                    recipients = variable_value  # pyright: ignore[reportAssignmentType]
                    log.info("recipients_resolved", recipients=recipients)

        return recipients

    def register_submission(self, submission: Submission, options: Options) -> None:
        config = EmailConfig.get_solo()
        config.apply_defaults_to(options)

        recipients = self.get_recipients(submission, options)
        self.send_registration_email(recipients, submission, options)

        # ensure that the payment email is also sent if registration is deferred until
        # payment is completed
        global_config = GlobalConfiguration.get_solo()
        if (
            global_config.wait_for_payment_to_register
            and submission.payment_user_has_paid
        ):
            self.update_payment_status(submission=submission, options=options)

    @staticmethod
    def render_registration_email(
        submission: Submission, is_payment_update: bool, extra_context=None
    ):
        if extra_context is None:
            extra_context = {}

        templates = get_registration_email_templates(submission)

        # common kwargs and context
        renderer_kwargs = {
            "submission": submission,
            "mode": RenderModes.registration,
        }
        base_context = {
            "public_reference": submission.public_registration_reference,
            "completed_on": timezone.localtime(submission.completed_on).strftime(
                "%H:%M:%S %d-%m-%Y"
            ),
            "submission_language": get_language_info(submission.language_code)[
                "name_translated"
            ],
            "co_signer": submission.get_co_signer(),
            **get_variables_for_context(submission),
            "_form": submission.form,
            "_submission": submission,
        }

        # Render the subject
        subject = render_from_string(
            templates.payment_subject if is_payment_update else templates.subject,
            context={**base_context, **extra_context},
            disable_autoescape=True,
        )

        # HTML mode
        html_renderer = Renderer(as_html=True, **renderer_kwargs)
        html_content = render_email_template(
            template=templates.content_html,
            context={
                **base_context,
                "renderer": html_renderer,
                "rendering_text": False,
                **extra_context,
            },
        )

        # Plain text mode
        text_renderer = Renderer(as_html=False, **renderer_kwargs)
        text_content = render_email_template(
            template=templates.content_text,
            context={
                **base_context,
                "renderer": text_renderer,
                "rendering_text": True,
                **extra_context,
            },
        )
        # post process since the mail template has html markup and django escaped entities
        text_content = strip_tags_plus(text_content, keep_leading_whitespace=True)
        text_content = html.unescape(text_content)

        return subject, html_content, text_content

    def send_registration_email(
        self,
        recipients: list[str],
        submission: Submission,
        options: Options,
        extra_context: dict[str, Any] | None = None,
        is_payment_update: bool = False,
    ) -> None:
        subject, html_content, text_content = self.render_registration_email(
            submission, extra_context=extra_context, is_payment_update=is_payment_update
        )

        attachments = []

        # per form or global default to attach file uploads to the e-mail directly.
        # NOTE that it's explicitly the responsibility of the form designer to ensure
        # the total attachment size is below the SMTP server limit. We do not perform
        # any checking of that as it'd rely on complex configuration and/or guesswork.
        if options.get("attach_files_to_email"):
            attachments += [
                (
                    file_attachment.get_display_name(),
                    file_attachment.content.read(),
                    file_attachment.content_type,
                )
                for file_attachment in submission.attachments
            ]

        attachment_formats = options.get("attachment_formats", [])
        for attachment_format in attachment_formats:
            mime_type = types_map[f".{attachment_format}"]
            if attachment_format in [AttachmentFormat.csv, AttachmentFormat.xlsx]:
                qs = Submission.objects.filter(pk=submission.pk).select_related(
                    "auth_info"
                )
                export_data = create_submission_export(qs).export(attachment_format)

                attachment = (
                    f"{submission.form.admin_name} - submission.{attachment_format}",
                    export_data,
                    mime_type,
                )
                attachments.append(attachment)
            elif attachment_format == AttachmentFormat.pdf:
                attachment = (
                    f"{submission.report.title}.pdf",
                    submission.report.content.read(),
                    mime_type,
                )
                attachments.append(attachment)
        send_mail_html(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
            attachment_tuples=attachments,
            text_message=text_content,
            extra_headers={
                "Content-Language": submission.language_code,
                X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                X_OF_CONTENT_UUID_HEADER: str(submission.uuid),
                X_OF_EVENT_HEADER: EmailEventChoices.registration,
            },
        )

    def update_payment_status(self, submission: "Submission", options: Options):
        recipients = options.get("payment_emails")

        if not recipients:
            recipients = self.get_recipients(submission, options)

        order_ids = submission.payments.get_completed_public_order_ids()
        extra_context = {
            # switch in the template
            "payment_received": True,
            # note: it is not a feature (yet) but the model supports multiple payments
            "payment_order_id": ", ".join(order_ids),
        }
        self.send_registration_email(
            recipients, submission, options, extra_context, is_payment_update=True
        )

    def check_config(self):
        check_config()

    def get_config_actions(self) -> list[Action]:
        return [
            (_("Test"), reverse("admin_email_test")),
        ]

    def get_custom_templatetags_libraries(self) -> list[str]:
        return [
            "openforms.registrations.contrib.email.templatetags.registrations.contrib.email.registration_summary"
        ]
