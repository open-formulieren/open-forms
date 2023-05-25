import logging

from django.conf import settings
from django.utils.translation import ugettext

from celery import chain

from openforms.celery import app
from openforms.emails.utils import render_email_template, send_mail_html
from openforms.logging import logevent
from openforms.submissions.models import Submission

from .cleanup import *  # noqa
from .emails import *  # noqa
from .registration import *  # noqa

logger = logging.getLogger(__name__)

__all__ = ["send_email_cosigner", "on_cosign"]


@app.task()
def send_email_cosigner(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    if not (recipient := submission.cosigner_email):
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
        logevent.cosigner_email_queuing_failure(submission)
        raise

    logevent.cosigner_email_queuing_success(submission)


def on_cosign(submission_id: int) -> None:
    register_submission_task = register_submission.si(submission_id)
    # TODO ADD cosigner to CC
    send_confirmation_email_task = maybe_send_confirmation_email.si(submission_id)
    # TODO Should it hash the cosigner data attributes?
    hash_identifying_attributes_task = maybe_hash_identifying_attributes.si(
        submission_id
    )

    on_cosign_chain = chain(
        register_submission_task,
        send_confirmation_email_task,
        hash_identifying_attributes_task,
    )

    on_cosign_chain.delay()
