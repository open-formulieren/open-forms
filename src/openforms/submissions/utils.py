import logging
from contextlib import contextmanager
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import caches
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

# with the interval of 0.1s, this gives us 2.0 / 0.1 = 20 concurrent requests,
# which is far above the typical browser concurrency mode (~6-8 requests).
SESSION_LOCK_TIMEOUT_SECONDS = 2.0


@contextmanager
def _session_lock(session: SessionBase, key: str):
    """
    Helper to manage session data mutations for the specified key.

    Concurrent session updates see stale data from when the request initially
    got processed, so any added items from parallel requests is not taken into
    account. This context manager refreshes the session data just-in-time and uses
    a Redis distributed lock to synchronize access.

    .. note:: this is pretty deep in Django internals, there doesn't appear to be a
       public API for things like these :(
    """
    # only existing session have an existing key. If this is a new session, it hasn't
    # been persisted to the backend yet, so there is also no possible race condition.
    is_new = session.session_key is None
    if is_new:
        yield
        return

    # See TODO in settings about renaming this cache
    redis_cache = caches["portalocker"]

    # make the lock tied to the session itself, so that we don't affect other people's
    # sessions.
    cache_key = f"django:session-update:{session.session_key}"

    # this is... tricky. To ensure we aren't still operating on stale data, we refresh
    # the session data after acquiring a lock so that we're the only one that will be
    # writing to it.
    #
    # For the locking interface, see redis-py :meth:`redis.client.Redis.lock`

    logger.debug("Acquiring session lock for session %s", session.session_key)
    with redis_cache.lock(
        cache_key,
        # max lifetime for the lock itself, must always be provided in case something
        # crashes and we fail to call release
        timeout=SESSION_LOCK_TIMEOUT_SECONDS,
        # wait rather than failing immediately, we are trying to handle parallel
        # requests here. Can't explicitly specify this, see
        # https://github.com/jazzband/django-redis/issues/596. redis-py default is True.
        # blocking=True,
        # how long we can try to acquire the lock
        blocking_timeout=SESSION_LOCK_TIMEOUT_SECONDS,
    ):
        logger.debug("Got session lock for session %s", session.session_key)
        # nasty bit... the session itself can already be modified with *other*
        # information that isn't relevant. So, we load the data from the storage again
        # and only look at the provided key. If that one is different, we update our
        # local data. We can not just reset to the result of session.load(), as that
        # would discard modifications that should be persisted.
        persisted_data = session.load()
        if (data_slice := persisted_data.get(key)) != (current := session.get(key)):
            logger.debug(
                "Data from storage is different than what we currently have. "
                "Session %s, key '%s' - in storage: %s, our view: %s",
                session.session_key,
                key,
                data_slice,
                current,
            )
            session[key] = data_slice
            logger.debug(
                "Updated key '%s' from storage for session %s", key, session.session_key
            )

        # execute the calling code and exit, clearing the lock.
        yield

        logger.debug(
            "New session data for session %s is: %s",
            session.session_key,
            session._session,
        )

        # ensure we save in-between to persist the modifications, before the request
        # may even be finished
        session.save()
        logger.debug("Saved session data for session %s", session.session_key)


def append_to_session_list(session: SessionBase, session_key: str, value: Any) -> None:
    with _session_lock(session, session_key):
        active = session.get(session_key, [])
        if value not in active:
            active.append(value)
            session[session_key] = active


def remove_from_session_list(
    session: SessionBase, session_key: str, value: Any
) -> None:
    with _session_lock(session, session_key):
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
            theme=submission.form.theme,
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
    variables = state.get_variables()

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
    request: HttpRequest | Request,
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
