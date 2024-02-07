from typing import Any

from django.dispatch import receiver
from django.http import HttpRequest

from hijack.signals import hijack_ended, hijack_started

from openforms.logging import logevent

from .models import User


@receiver(hijack_started, dispatch_uid="hijack_started.manage_totp_device")
def handle_hijack_start(
    sender: None, hijacker: User, hijacked: User, request: HttpRequest, **kwargs: Any
):
    """
    Add an audit trail entry for the hijack action.

    Malicious actors can then not hijack another user and view potentially sensitive
    data causing only the hijacked user to show up in the audit log instead of the
    hijacker.
    """
    logevent.hijack_started(hijacker, hijacked)


@receiver(hijack_ended, dispatch_uid="hijack_ended.manage_totp_device")
def handle_hijack_end(
    sender: None, hijacker: User, hijacked: User, request: HttpRequest, **kwargs: Any
):
    """
    Add an audit trail entry for the hijack action.

    Malicious actors can then not hijack another user and view potentially sensitive
    data causing only the hijacked user to show up in the audit log instead of the
    hijacker.
    """
    logevent.hijack_ended(hijacker, hijacked)
