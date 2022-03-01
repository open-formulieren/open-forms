import logging

from django.core.exceptions import PermissionDenied
from django.dispatch import Signal, receiver
from django.utils.translation import gettext_lazy as _

from rest_framework.request import Request

from openforms.submissions.models import Submission
from openforms.submissions.signals import submission_complete, submission_start

from .constants import FORM_AUTH_SESSION_KEY
from .registry import register
from .utils import store_auth_details

logger = logging.getLogger(__name__)

#
# Custom signals
#
co_sign_authentication_success = Signal()
"""
Signal a succesful co-sign authentication.

Provides:
    :arg request: the HttpRequest instance
    :arg plugin: authentication plugin identifier
    :arg submission: The :class:`Submission` instance being co-signed.
"""


#
# Signal handlers
#


@receiver(submission_start, dispatch_uid="auth.set_submission_form_auth")
def set_auth_attribute_on_session(
    sender, instance: Submission, request: Request, **kwargs
):
    form_auth = request.session.get(FORM_AUTH_SESSION_KEY)
    if not form_auth:
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

    logger.debug(
        "Persisting form auth to submission %s. Plugin: '%s' (setting attribute '%s')",
        instance.uuid,
        plugin,
        attribute,
    )
    store_auth_details(instance, form_auth)


@receiver(submission_complete, dispatch_uid="auth.clean_submission_form_auth")
def clean_submission_form_auth(sender, request: Request, **kwargs):
    if FORM_AUTH_SESSION_KEY not in request.session:
        return

    del request.session[FORM_AUTH_SESSION_KEY]
