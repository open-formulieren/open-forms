import logging

from django.core.exceptions import PermissionDenied
from django.dispatch import Signal, receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework.request import Request

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
from .utils import (
    remove_auth_info_from_session,
    store_auth_details,
    store_registrator_details,
)

logger = logging.getLogger(__name__)

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
    if anonymous:
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
    if plugin_instance.is_demo_plugin and not request.user.is_staff:
        logger.warning(
            "Demo plugin '%s' auth flow bypassed, blocking attempt to set identifying "
            "attribute on submission '%s'.",
            plugin,
            instance.uuid,
        )
        raise PermissionDenied(_("Demo plugins require an active admin session."))

    user = request.user if request.user.is_authenticated else None
    logger.debug(
        "Persisting form auth to submission %s. Plugin: '%s' (setting attribute '%s')",
        instance.uuid,
        plugin,
        attribute,
        extra={
            "user_id": user.id if user else None,
            "submission_uuid": instance.uuid,
            "plugin": plugin,
            "attribute": attribute,
        },
    )
    logevent.submission_auth(
        instance,
        delegated=bool(
            registrator_subject
            and registrator_subject.get("skipped_subject_info") is None
        ),
        user=user,
    )

    if registrator_subject:
        # we got registrator_subject data so form_auth is an employee
        if registrator_subject.get("skipped_subject_info"):
            # If continued without extra details, store the employee details in AuthInfo
            store_auth_details(instance, form_auth)
        else:
            # If KVK/BSN is given, store those details in the AuthInfo model and the employee details in the Registrator model.
            auth_save = {
                "value": registrator_subject["value"],
                "attribute": registrator_subject["attribute"],
                # TODO we don't have a plugin to define here? things break if this doesn't exist (like the logout view)
                "plugin": registrator_subject.get("plugin", "registrator"),
            }
            registrator_save = {
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
    [submission_complete, authentication_logout],
    dispatch_uid="auth.clean_submission_auth",
)
def clean_submission_auth(sender, request: Request, **kwargs):
    if FORM_AUTH_SESSION_KEY in request.session:
        del request.session[FORM_AUTH_SESSION_KEY]

    if REGISTRATOR_SUBJECT_SESSION_KEY in request.session:
        del request.session[REGISTRATOR_SUBJECT_SESSION_KEY]


@receiver(submission_cosigned, dispatch_uid="auth.set_submission_form_auth")
def set_cosign_data_on_submission(
    sender, instance: Submission, request: Request, **kwargs
):
    form_auth = request.session.get(FORM_AUTH_SESSION_KEY)

    instance.co_sign_data = form_auth
    instance.co_sign_data["cosign_date"] = timezone.now().isoformat()
    instance.save()

    remove_auth_info_from_session(request)
