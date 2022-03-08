from io import StringIO

from django.apps import AppConfig, apps
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.management import create_contenttypes
from django.core.management import call_command
from django.db.models.signals import post_migrate

from django_otp import DEVICE_ID_SESSION_KEY


def update_admin_index(sender, **kwargs):
    from django_admin_index.models import AppGroup

    AppGroup.objects.all().delete()

    # Make sure project models are registered.
    project_name = __name__.split(".")[0]

    for app_config in apps.get_app_configs():
        if app_config.name.startswith(project_name):
            create_contenttypes(app_config, verbosity=0)

    call_command("loaddata", "default_admin_index", verbosity=0, stdout=StringIO())


def update_groups(sender, **kwargs):
    # Make sure project permissions are created.
    project_name = __name__.split(".")[0]

    for app_config in apps.get_app_configs():
        if app_config.name.startswith(project_name):
            create_permissions(app_config, verbosity=0)

    call_command("loaddata", "default_groups", verbosity=0, stdout=StringIO())


def _set_session_device(request, device):
    request.session[DEVICE_ID_SESSION_KEY] = device.persistent_id


def handle_hijack_start(sender, hijacker, hijacked, request, **kwargs):
    """
    Potentially add a dummy hijack device to ensure two-factor hijacking.
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice

    hijack_device, _ = TOTPDevice.objects.get_or_create(
        user=hijacked,
        name="hijack_device",
    )
    _set_session_device(request, hijack_device)


def handle_hijack_end(sender, hijacker, hijacked, request, **kwargs):
    """
    1. Remove any dummy OTP devices for the hijacked user.
    2. Restore the original OTP device for the hijacker.
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice

    TOTPDevice.objects.filter(user=hijacked, name="hijack_device").delete()

    try:
        device = TOTPDevice.objects.get(user=hijacker)
        _set_session_device(request, device)
    except TOTPDevice.DoesNotExist:
        pass


class AccountsConfig(AppConfig):
    name = "openforms.accounts"

    def ready(self):
        post_migrate.connect(update_admin_index, sender=self)
        post_migrate.connect(update_groups, sender=self)

        from hijack.signals import hijack_ended, hijack_started

        hijack_started.connect(handle_hijack_start)
        hijack_ended.connect(handle_hijack_end)
