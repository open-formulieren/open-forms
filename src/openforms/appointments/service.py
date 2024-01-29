"""
Public API of the appointments module.

The exported names here may be used in other django apps and/or Open Forms modules.
Anything else is considered private API.
"""

from openforms.submissions.models import Submission

from .renderer import AppointmentRenderer
from .utils import get_appointment, get_plugin

__all__ = [
    "AppointmentRenderer",
    "get_appointment",
    "get_email_confirmation_recipients",
    "get_plugin",
]


def get_email_confirmation_recipients(submission: Submission) -> list[str]:
    """
    Extract confirmation email recipient addresses, if relevant.

    If the submission is for a form that is not a (new-style) appointment form, an
    empty list is returned. The caller is expected to apply different logic to obtain
    the e-mail addresses.
    """
    if (appointment := get_appointment(submission)) is None:
        return []
    return appointment.extract_email_addresses()
