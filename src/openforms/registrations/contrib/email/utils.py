from openforms.config.models import GlobalConfiguration


def get_registration_email_templates(submission):
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
        return (
            subject_template,
            payment_subject_template,
            submission.form.registration_email_content_html,
            submission.form.registration_email_content_text,
        )

    return (
        subject_template,
        payment_subject_template,
        config.registration_email_content_html,
        config.registration_email_content_text,
    )
