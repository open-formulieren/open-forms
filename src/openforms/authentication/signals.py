from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.dispatch import Signal, receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from rest_framework.request import Request

from openforms.accounts.models import User
from openforms.logging import logevent
from openforms.submissions.models import Submission
from openforms.submissions.signals import (
    submission_complete,
    submission_cosigned,
    submission_resumed,
    submission_start,
)

from .constants import FORM_AUTH_SESSION_KEY, REGISTRATOR_SUBJECT_SESSION_KEY
from .registry import register
from .typing import BaseAuth, FormAuth
from .utils import (
    logout_submission,
    remove_auth_info_from_session,
    store_auth_details,
    store_registrator_details,
)

logger = structlog.stdlib.get_logger(__name__)

#
# Custom signals
#
authentication_success = Signal()
co_sign_authentication_success = Signal()
"""
Signal a successful co-sign authentication.

Provides:
    :arg request: the HttpRequest instance
    :arg plugin: authentication plugin identifier
    :arg submission: The :class:`Submission` instance being co-signed.
"""
authentication_logout = Signal()
"""
Signals that a user that had logged in with an authentication plugin logged out.

Provides:
    :arg request: the HttpRequest instance
"""


#
# Signal handlers
#


@receiver(
    [submission_start, submission_resumed], dispatch_uid="auth.set_submission_form_auth"
)
def set_auth_attribute_on_session(
    sender, instance: Submission, request: Request, anonymous=False, **kwargs
):
    assert isinstance(request.user, User | AnonymousUser)
    log = logger.bind(submission_uuid=str(instance.uuid), anonymous=anonymous)
    if anonymous:
        log.info("authentication.skip_storing_auth_info")
        return

    # form_auth has information from an authentication backend, so could be a client or employee
    form_auth = request.session.get(FORM_AUTH_SESSION_KEY)

    # registrator_subject might have additional info about the client entered by an employee
    registrator_subject = request.session.get(REGISTRATOR_SUBJECT_SESSION_KEY)

    if not form_auth:
        if instance.form.login_required:
            raise PermissionDenied(_("You must be logged in to start this form."))
        return

    plugin = form_auth["plugin"]
    attribute = form_auth["attribute"]
    plugin_instance = register[plugin]

    log = log.bind(plugin=plugin_instance, attribute=attribute)
    if plugin_instance.is_demo_plugin and not request.user.is_staff:
        log.warning(
            "authentication.block_storing_auth_info",
            reason="demo_plugin_requires_staff_user",
            user=request.user,
        )
        raise PermissionDenied(_("Demo plugins require an active admin session."))

    user = request.user if request.user.is_authenticated else None
    assert isinstance(user, User | None)
    is_delegated = bool(
        registrator_subject and registrator_subject.get("skipped_subject_info") is None
    )
    log.debug("authentication.submission_auth", is_delegated=is_delegated)
    logevent.submission_auth(instance, delegated=is_delegated, user=user)

    if registrator_subject:
        # we got registrator_subject data so form_auth is an employee
        if registrator_subject.get("skipped_subject_info"):
            # If continued without extra details, store the employee details in AuthInfo
            store_auth_details(instance, form_auth)
        else:
            # If KVK/BSN is given, store those details in the AuthInfo model and the employee details in the Registrator model.
            auth_save: FormAuth = {
                "value": registrator_subject["value"],
                "attribute": registrator_subject["attribute"],
                # TODO we don't have a plugin to define here? things break if this doesn't exist (like the logout view)
                "plugin": registrator_subject.get("plugin", "registrator"),
            }
            registrator_save: BaseAuth = {
                "value": form_auth["value"],
                "attribute": form_auth["attribute"],
                "plugin": form_auth["plugin"],
            }
            store_auth_details(instance, auth_save)
            store_registrator_details(instance, registrator_save)
    else:
        store_auth_details(instance, form_auth)

    # After the authentication details have been attached to the submission, the session
    # no longer has to keep track of this information, because the user could start another
    # form with different / no authentication
    remove_auth_info_from_session(request)


@receiver(
    authentication_logout,
    dispatch_uid="auth.clean_submission_auth",
)
def clean_submission_auth(sender, request: Request, **kwargs):
    if FORM_AUTH_SESSION_KEY in request.session:
        del request.session[FORM_AUTH_SESSION_KEY]

    if REGISTRATOR_SUBJECT_SESSION_KEY in request.session:
        del request.session[REGISTRATOR_SUBJECT_SESSION_KEY]


@receiver(submission_complete, dispatch_uid="auth.logout_after_submission")
def logout_after_submission(sender, instance: Submission, request: Request, **kwargs):
    logout_submission(submission=instance, request=request)


@receiver(submission_cosigned, dispatch_uid="auth.set_submission_form_auth")
def set_cosign_data_on_submission(
    sender, instance: Submission, request: Request, **kwargs
):
    form_auth = request.session.get(FORM_AUTH_SESSION_KEY)
    assert form_auth is not None

    instance.co_sign_data = {
        "version": "v2",
        **form_auth,
        "cosign_date": timezone.now().isoformat(),
    }
    instance.full_clean()  # run validation to ensure the shape is as documented (!)
    instance.save()

    remove_auth_info_from_session(request)
