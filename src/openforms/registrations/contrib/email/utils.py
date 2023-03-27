from openforms.config.models import GlobalConfiguration


def get_registration_email_templates(submission):
    templates = (
        submission.form.registration_email_subject,
        submission.form.registration_email_payment_subject,
        submission.form.registration_email_content_html,
        submission.form.registration_email_content_text,
    )

    if all(templates):
        return templates

    config = GlobalConfiguration.get_solo()
    return (
        config.registration_email_subject,
        config.registration_email_payment_subject,
        config.registration_email_content_html,
        config.registration_email_content_text,
    )
