from dataclasses import dataclass

from openforms.submissions.models import Submission

from .models import EmailConfig


@dataclass
class RegistrationEmailTemplates:
    subject: str
    payment_subject: str
    content_html: str
    content_text: str


def get_registration_email_templates(
    submission: Submission,
) -> RegistrationEmailTemplates:
    global_config = EmailConfig.get_solo()

    backend = submission.registration_backend
    if backend is not None:
        form_config = backend.options
    else:
        form_config = {}

    subject_template = form_config.get("email_subject") or global_config.subject
    payment_subject_template = (
        form_config.get("email_payment_subject") or global_config.payment_subject
    )

    html_body = (
        form_template_html
        if (form_template_html := form_config.get("email_content_template_html"))
        else global_config.content_html
    )
    text_body = (
        form_config["email_content_template_text"]
        if form_template_html
        else global_config.content_text
    )
    return RegistrationEmailTemplates(
        subject=subject_template,
        payment_subject=payment_subject_template,
        content_html=html_body,
        content_text=text_body,
    )
