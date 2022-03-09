from django.dispatch import receiver

from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from hijack.signals import hijack_ended, hijack_started

from openforms.logging import logevent


def _set_session_device(request, device):
    request.session[DEVICE_ID_SESSION_KEY] = device.persistent_id


@receiver(hijack_started, dispatch_uid="hijack_started.manage_totp_device")
def handle_hijack_start(sender, hijacker, hijacked, request, **kwargs):
    """
    Potentially add a dummy hijack device to ensure two-factor hijacking.
    """
    # add hijack actions to audit log - malicious actors can then not hijack another
    # user and view potentially sensitive data causing them to show up in the audit log
    logevent.hijack_started(hijacker, hijacked)

    hijack_device, _ = TOTPDevice.objects.get_or_create(
        user=hijacked,
        name="hijack_device",
    )
    _set_session_device(request, hijack_device)


@receiver(hijack_ended, dispatch_uid="hijack_ended.manage_totp_device")
def handle_hijack_end(sender, hijacker, hijacked, request, **kwargs):
    """
    1. Remove any dummy OTP devices for the hijacked user.
    2. Restore the original OTP device for the hijacker.
    """
    # add hijack actions to audit log - malicious actors can then not hijack another
    # user and view potentially sensitive data causing them to show up in the audit log
    logevent.hijack_ended(hijacker, hijacked)

    TOTPDevice.objects.filter(user=hijacked, name="hijack_device").delete()

    try:
        device = TOTPDevice.objects.get(user=hijacker)
        _set_session_device(request, device)
    except TOTPDevice.DoesNotExist:
        pass
