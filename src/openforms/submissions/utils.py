from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import caches
from django.http import HttpRequest
from django.utils import translation

import structlog
from furl import furl
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.emails.confirmation_emails import (
    get_confirmation_email_context_data,
    get_confirmation_email_templates,
)
from openforms.emails.constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from openforms.emails.utils import (
    render_email_template,
    send_mail_html,
    strip_tags_plus,
)
from openforms.formio.service import FormioData
from openforms.forms.models import Form
from openforms.logging import logevent
from openforms.utils.urls import build_absolute_uri

from .constants import SUBMISSIONS_SESSION_KEY
from .exceptions import FormDeactivated, FormMaintenance, FormMaximumSubmissions
from .models import (
    Submission,
    SubmissionReport,
    SubmissionValueVariable,
)
from .tokens import submission_report_token_generator

logger = structlog.stdlib.get_logger(__name__)

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

    log = logger.bind(
        action="submissions.session_lock", session_key=session.session_key
    )
    log.debug("acquiring_lock")
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
        log.debug("lock_acquired")
        # nasty bit... the session itself can already be modified with *other*
        # information that isn't relevant. So, we load the data from the storage again
        # and only look at the provided key. If that one is different, we update our
        # local data. We can not just reset to the result of session.load(), as that
        # would discard modifications that should be persisted.
        persisted_data = session.load()
        if (data_slice := persisted_data.get(key)) != (current := session.get(key)):
            log.debug(
                "stored_data_mismatch", key=key, in_storage=data_slice, our_view=current
            )
            session[key] = data_slice
            log.debug("data_updated", key=key)

        # execute the calling code and exit, clearing the lock.
        yield

        log.debug("session_updated", keys=list(session.keys()))

        # ensure we save in-between to persist the modifications, before the request
        # may even be finished
        session.save()
        log.debug("session_saved")


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


def send_confirmation_email(submission: Submission) -> None:
    logevent.confirmation_email_start(submission)

    subject_template, content_template = get_confirmation_email_templates(submission)

    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "skip_confirmation_email",
            reason="could_not_determine_recipient_email_address",
            submission_uuid=str(submission.uuid),
        )
        logevent.confirmation_email_skip(submission)

        submission.confirmation_email_sent = False
        submission.save(update_fields=["confirmation_email_sent"])
        return

    cc_emails = []
    cosign = submission.cosign_state
    should_cosigner_be_in_cc = (
        cosign.is_signed and not submission.cosign_confirmation_email_sent
    )
    if should_cosigner_be_in_cc and (cosigner_email := cosign.email):
        cc_emails.append(cosigner_email)

    context = get_confirmation_email_context_data(submission)

    # render the templates with the submission context
    with translation.override(submission.language_code):
        subject = render_email_template(
            subject_template, context, rendering_text=True, disable_autoescape=True
        ).strip()

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
            extra_headers={
                "Content-Language": submission.language_code,
                X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                X_OF_CONTENT_UUID_HEADER: str(submission.uuid),
                X_OF_EVENT_HEADER: EmailEventChoices.confirmation,
            },
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
    SubmissionValueVariable.objects.bulk_create(
        [
            variable
            for variable in state.user_defined_variables.values()
            if not variable.pk
        ]
    )


def persist_user_defined_variables(submission: Submission) -> None:
    state = submission.load_submission_value_variables_state()
    user_defined_vars_data = FormioData(
        {
            variable.key: variable.value
            for variable in state.user_defined_variables.values()
        }
    )

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
    :raises: :class:`FormMaximumSubmissions` if the form has reached the maximum amount
      of submissions.
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

    # do not proceed if the form has reached the maximum number of submissions
    if form.submissions_limit_reached:
        raise FormMaximumSubmissions()


def get_report_download_url(request: Request, report: SubmissionReport) -> str:
    token = submission_report_token_generator.make_token(report)
    download_url = reverse(
        "submissions:download-submission",
        kwargs={"report_id": report.id, "token": token},
    )
    return request.build_absolute_uri(download_url)


def get_filtered_submission_admin_url(
    form_id: int, *, filter_retry: bool, registration_time: str
) -> str:
    query_params = {
        "form__id__exact": form_id,
        "needs_on_completion_retry__exact": 1 if filter_retry else 0,
        "registration_time": registration_time,
    }
    submissions_relative_admin_url = furl(
        reverse("admin:submissions_submission_changelist")
    )
    submissions_relative_admin_url.add(query_params)

    return build_absolute_uri(submissions_relative_admin_url.url)
