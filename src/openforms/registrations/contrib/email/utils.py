from dataclasses import dataclass

from .models import EmailConfig


@dataclass
class RegistrationEmailTemplates:
    subject: str
    payment_subject: str
    content_html: str
    content_text: str


def get_registration_email_templates(submission) -> RegistrationEmailTemplates:
    config = EmailConfig.get_solo()

    form_options = submission.form.registration_backend_options

    subject_template = form_options.get("email_subject") or config.subject
    payment_subject_template = (
        form_options.get("email_payment_subject") or config.payment_subject
    )

    if any(
        [
            form_options.get("email_content_template_html"),
            form_options.get("email_content_template_text"),
        ]
    ):
        return RegistrationEmailTemplates(
            subject=subject_template,
            payment_subject=payment_subject_template,
            content_html=form_options.get("email_content_template_html"),
            content_text=form_options.get("email_content_template_text"),
        )

    return RegistrationEmailTemplates(
        subject=subject_template,
        payment_subject=payment_subject_template,
        content_html=config.content_html,
        content_text=config.content_text,
    )
