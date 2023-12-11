import logging
from typing import Any, Union

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpRequest
from django.utils import translation

from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.appointments.utils import get_confirmation_mail_suffix
from openforms.emails.confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
)
from openforms.emails.utils import (
    render_email_template,
    send_mail_html,
    strip_tags_plus,
)
from openforms.forms.models import Form
from openforms.logging import logevent
from openforms.variables.constants import FormVariableSources

from .constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from .exceptions import FormDeactivated, FormMaintenance
from .form_logic import check_submission_logic
from .models import (
    Submission,
    SubmissionReport,
    SubmissionValueVariable,
    TemporaryFileUpload,
)
from .tokens import submission_report_token_generator

logger = logging.getLogger(__name__)


def append_to_session_list(session: SessionBase, session_key: str, value: Any) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value not in active:
        active.append(value)
        session[session_key] = active


def remove_from_session_list(
    session: SessionBase, session_key: str, value: Any
) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value in active:
        active.remove(value)
        session[session_key] = active


def add_submmission_to_session(submission: Submission, session: SessionBase) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    append_to_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def remove_submission_from_session(
    submission: Submission, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def add_upload_to_session(upload: TemporaryFileUpload, session: SessionBase) -> None:
    """
    Store the upload UUID in the request session for authorization checks.
    """
    append_to_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_upload_from_session(
    upload: TemporaryFileUpload, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_submission_uploads_from_session(
    submission: Submission, session: SessionBase
) -> None:
    for attachment in submission.get_attachments().filter(temporary_file__isnull=False):
        remove_upload_from_session(attachment.temporary_file, session)


def send_confirmation_email(submission: Submission) -> None:
    logevent.confirmation_email_start(submission)

    subject_template, content_template = get_confirmation_email_templates(submission)

    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        logevent.confirmation_email_skip(submission)
        return

    cc_emails = []
    should_cosigner_be_in_cc = (
        submission.cosign_complete and not submission.cosign_confirmation_email_sent
    )
    if should_cosigner_be_in_cc and (cosigner_email := submission.cosigner_email):
        cc_emails.append(cosigner_email)

    context = get_confirmation_email_context_data(submission)

    # render the templates with the submission context
    with translation.override(submission.language_code):
        subject = render_email_template(
            subject_template, context, rendering_text=True, disable_autoescape=True
        ).strip()

        if subject_suffix := get_confirmation_mail_suffix(submission):
            subject = f"{subject} {subject_suffix}"

        html_content = render_email_template(content_template, context)
        text_content = strip_tags_plus(
            render_email_template(content_template, context, rendering_text=True),
            keep_leading_whitespace=True,
        )

    try:
        send_mail_html(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
            to_emails,
            cc=cc_emails,
            text_message=text_content,
        )
    except Exception as e:
        logevent.confirmation_email_failure(submission, e)
        raise

    submission.confirmation_email_sent = True
    if should_cosigner_be_in_cc:
        submission.cosign_confirmation_email_sent = True
    if submission.payment_required and submission.payment_user_has_paid:
        submission.payment_complete_confirmation_email_sent = True

    submission.save(
        update_fields=(
            "confirmation_email_sent",
            "cosign_confirmation_email_sent",
            "payment_complete_confirmation_email_sent",
        )
    )

    logevent.confirmation_email_success(submission)


def initialise_user_defined_variables(submission: Submission):
    state = submission.load_submission_value_variables_state()
    variables = {
        variable_key: variable
        for variable_key, variable in state.variables.items()
        if variable.form_variable.source == FormVariableSources.user_defined
    }
    SubmissionValueVariable.objects.bulk_create(
        [variable for key, variable in variables.items() if not variable.pk]
    )


def persist_user_defined_variables(
    submission: "Submission", request: "Request"
) -> None:
    data = submission.data

    last_form_step = submission.submissionstep_set.order_by("form_step__order").last()
    if not last_form_step:
        return

    check_submission_logic(submission, data)

    state = submission.load_submission_value_variables_state()
    variables = state.variables

    user_defined_vars_data = {
        variable.key: variable.value
        for variable_key, variable in variables.items()
        if variable.form_variable
        and variable.form_variable.source == FormVariableSources.user_defined
    }

    if user_defined_vars_data:
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            user_defined_vars_data, submission
        )


def check_form_status(
    request: Union[HttpRequest, Request],
    form: Form,
    include_safe_methods: bool = False,
) -> None:
    """
    Verify the availability of the submission's form.

    Forms can be set to maintenance mode or be deactivated while a submission
    is not completed - this has an impact on different types of users:

    * Nobody can fill out/continue deactivated forms
    * Staff users can continue filling out a form in maintenance mode, while
      non-staff are blocked from doing so.

    :raises: :class:`FormDeactivated` if the form is deactivated
    :raises: :class`FormMaintenance` if the form is in maintenance mode and the user
      is not a staff user.
    """
    # live forms -> shortcut, this is okay, proceed as usual
    if form.is_available:
        return

    # only block for write operations
    if not include_safe_methods and request.method in SAFE_METHODS:
        return

    if not form.active:
        raise FormDeactivated()

    # do not clear the submission from the session, as maintenance mode is supposed
    # to pass after a while
    if form.maintenance_mode and not request.user.is_staff:
        raise FormMaintenance()


def get_report_download_url(request: Request, report: SubmissionReport) -> str:
    token = submission_report_token_generator.make_token(report)
    download_url = reverse(
        "api:submissions:download-submission",
        kwargs={"report_id": report.id, "token": token},
    )
    return request.build_absolute_uri(download_url)
