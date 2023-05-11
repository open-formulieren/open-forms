import logging

from django.conf import settings
from django.utils.translation import ugettext

from openforms.celery import app
from openforms.emails.utils import render_email_template, send_mail_html
from openforms.logging import logevent
from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)

__all__ = ["send_email_cosigner"]


@app.task()
def send_email_cosigner(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    recipient = submission.get_cosigner_email()
    if not recipient:
        logger.warning(
            "No co-signer email found in the form. Skipping co-sign email for submission %d.",
            submission.id,
        )
        return

    # Send Co-sign email # TODO add configurable templates
    content = render_email_template(
        ugettext(
            'This is a request to co-sign form "{{ form_name }}". Please go to the webpage of this form on our '
            "website and click on the 'co-sign' button. You will then be redirected to authenticate yourself."
            "After authentication, fill in the following code to retrieve the form submission:\n\n{{ code }}\n\n."
        ),
        context={
            "code": submission.public_registration_reference,
            "form_name": submission.form.name,
        },
    )

    try:
        send_mail_html(
            subject=f"Co-sign request for {submission.form.name}",
            html_body=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            text_message=content,
        )
    except Exception:
        logevent.cosigner_email_failure(submission)
        raise

    logevent.cosigner_email_success(submission)
