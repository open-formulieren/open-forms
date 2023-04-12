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

    html_body = (
        form_template_html
        if (form_template_html := form_options.get("email_content_template_html"))
        else config.content_html
    )
    text_body = (
        form_options["email_content_template_text"]
        if form_template_html
        else config.content_text
    )
    return RegistrationEmailTemplates(
        subject=subject_template,
        payment_subject=payment_subject_template,
        content_html=html_body,
        content_text=text_body,
    )
