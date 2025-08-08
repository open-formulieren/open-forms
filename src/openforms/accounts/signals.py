from typing import Any, Literal

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest

from axes.signals import user_locked_out
from hijack.signals import hijack_ended, hijack_started

from openforms.logging import logevent

from .metrics import login_failures, logins, logouts, user_lockouts
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


@receiver(user_logged_in, dispatch_uid="user_logged_in.increment_counter")
def increment_logins_counter(
    sender: type[User], request: HttpRequest | None, user: User, **kwargs
) -> None:
    logins.add(
        1,
        attributes={
            "username": user.username,
            "http_target": request.path if request else "",
        },
    )


@receiver(user_logged_out, dispatch_uid="user_logged_out.increment_counter")
def increment_logouts_counter(
    sender: type[User], request: HttpRequest | None, user: User | None, **kwargs
) -> None:
    if user is None:
        return
    logouts.add(1, attributes={"username": user.username})


@receiver(user_login_failed, dispatch_uid="user_login_failed.increment_counter")
def increment_login_failure_counter(
    sender, request: HttpRequest | None = None, **kwargs
):
    login_failures.add(
        1,
        attributes={"http_target": request.path if request else ""},
    )


@receiver(user_locked_out, dispatch_uid="user_locked_out.increment_counter")
def increment_user_locked_out_counter(
    sender: Literal["axes"],
    request: HttpRequest,
    username: str,
    ip_address: str,
    **kwargs,
) -> None:
    user_lockouts.add(
        1,
        attributes={
            "http_target": request.path,
            "username": username,
        },
    )
