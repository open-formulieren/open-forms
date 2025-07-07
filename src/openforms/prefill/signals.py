from django.dispatch import receiver
from django.http import HttpRequest

import structlog

from openforms.authentication.base import BasePlugin
from openforms.authentication.signals import co_sign_authentication_success
from openforms.submissions.models import Submission

from .co_sign import add_co_sign_representation as _add_co_sign_representation

logger = structlog.stdlib.get_logger(__name__)


@receiver(
    co_sign_authentication_success,
    dispatch_uid="openforms.prefill.add_co_sign_representation",
)
def add_co_sign_representation(
    sender, request: HttpRequest, plugin: BasePlugin, submission: Submission, **kwargs
) -> None:
    log = logger.bind(
        action="prefill.add_co_sign_representation",
        submission_uuid=str(submission.uuid),
    )
    assert len(plugin.provides_auth) == 1
    log.debug("cosign", plugin_auth_type=plugin.provides_auth[0])
    if not submission.co_sign_data or not submission.co_sign_data["identifier"]:
        log.warning("cosign_data_missing_or_incomplete", outcome="skip")
        return

    _add_co_sign_representation(submission, plugin.provides_auth[0])
