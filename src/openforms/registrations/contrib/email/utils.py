from dataclasses import dataclass

from openforms.config.models import GlobalConfiguration


@dataclass
class RegistrationEmailTemplates:
    subject: str
    payment_subject: str
    content_html: str
    content_text: str


def get_registration_email_templates(submission) -> RegistrationEmailTemplates:
    config = GlobalConfiguration.get_solo()

    subject_template = (
        submission.form.registration_email_subject or config.registration_email_subject
    )
    payment_subject_template = (
        submission.form.registration_email_payment_subject
        or config.registration_email_payment_subject
    )

    if any(
        [
            submission.form.registration_email_content_html,
            submission.form.registration_email_content_text,
        ]
    ):
        return RegistrationEmailTemplates(
            subject=subject_template,
            payment_subject=payment_subject_template,
            content_html=submission.form.registration_email_content_html,
            content_text=submission.form.registration_email_content_text,
        )

    return RegistrationEmailTemplates(
        subject=subject_template,
        payment_subject=payment_subject_template,
        content_html=config.registration_email_content_html,
        content_text=config.registration_email_content_text,
    )
