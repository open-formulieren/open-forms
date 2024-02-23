import logging

from openforms.submissions.models import Submission

from .base import BasePlugin

__all__ = [
    "get_registration_plugin",
]

logger = logging.getLogger(__name__)


def get_registration_plugin(submission: Submission) -> BasePlugin | None:
    backend = submission.registration_backend

    if not backend:
        return

    registry = backend._meta.get_field("backend").registry
    return registry[backend.backend]
