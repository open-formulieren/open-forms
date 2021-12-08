import logging

from django.dispatch import receiver
from django.http import HttpRequest

from openforms.authentication.base import BasePlugin
from openforms.authentication.signals import co_sign_authentication_success
from openforms.submissions.models import Submission

from .co_sign import add_co_sign_representation as _add_co_sign_representation

logger = logging.getLogger(__name__)


@receiver(
    co_sign_authentication_success,
    dispatch_uid="openforms.prefill.add_co_sign_representation",
)
def add_co_sign_representation(
    sender, request: HttpRequest, plugin: BasePlugin, submission: Submission, **kwargs
) -> None:
    logger.debug(
        "Handling co-sign event for submisssion %s, plugin auth type: %s",
        submission.uuid,
        plugin.provides_auth,
    )

    if not submission.co_sign_data or not submission.co_sign_data["identifier"]:
        logger.warning(
            "Submission co sign data is missing or incomplete (submission %s), aborting",
            submission.uuid,
        )
        return

    _add_co_sign_representation(submission, plugin.provides_auth)
