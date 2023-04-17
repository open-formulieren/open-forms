import logging

from django.conf import settings

from glom import glom

from openforms.celery import app
from openforms.emails.utils import render_email_template, send_mail_html
from openforms.submissions.attachments import _iterate_data_with_components
from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)

__all__ = ["send_email_cosigner"]


@app.task()
def send_email_cosigner(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    co_sign_component = None
    component_data = None
    # Get email address
    for form_step in submission.form.formstep_set.select_related("form_definition"):
        for (
            component,
            upload_info,
            data_path,
            configuration_path,
        ) in _iterate_data_with_components(
            form_step.form_definition.configuration, submission.data
        ):
            if component["type"] == "cosign":
                co_sign_component = component
                component_data = glom(submission.data, data_path, default=None)
                break
        if co_sign_component:
            break
    else:
        logger.warning(
            "No co-sign component found in the form. Skipping co-sign email for submission %d.",
            submission.id,
        )
        return

    # TODO deal with co-sign component not filled in

    # Block submission for registration
    submission.waiting_on_cosign = True
    submission.save()

    # TODO Make code with BaseTokenGenerator

    # Send Co-sign email # TODO add configurable templates
    content = render_email_template(
        "Hi! This is the code {{ code }} and this is the URL: {{ link }}. Please co-sign!",
        context={
            "code": submission.public_registration_reference,
            "link": "http://test.test",
        },
    )
    recipient = component_data

    try:
        send_mail_html(
            subject="Please co-sign!",
            html_body=content,
            from_email=settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
            recipient_list=[recipient],
            text_message=content,
        )
    except Exception:
        # TODO add logging
        raise
