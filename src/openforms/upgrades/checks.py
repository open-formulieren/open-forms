from django.conf import settings
from django.core.checks import Error, Warning, register
from django.db import OperationalError, ProgrammingError

from .models import (
    VERSION_DEV,
    VERSION_LATEST,
    VERSION_UNKNOWN,
    VersionInfo,
    get_current_version,
)
from .upgrade_paths import VersionParseError, check_upgrade_path


def get_version_info():
    return VersionInfo.objects.only("current").get(pk=VersionInfo.singleton_instance_id)


@register()
def check_upgrade_possible(app_configs, **kwargs) -> list:
    """
    Check that upgrading from this version of the code is possible.

    The :class:`VersionInfo` model stores the version from the last upgrade,
    and we can get the current version of the code. We need to compare these against
    the supported upgrade paths and block upgrades if a path is not possible.

    System checks that raise errors prevent migrations from running, so an older
    version of the code can be deployed for a staggered upgrade path.
    """
    try:
        version_info = get_version_info()
    except (ProgrammingError, OperationalError):
        # the database table was not created yet. The query above selects only the
        # columns needed, so future migrations to the VersionInfo model don't crash
        # this check. We can reasonably assume that this is the first time the version
        # info is being used.
        return []
    except VersionInfo.DoesNotExist:
        # create the object the first time - we record the current version from code
        # as the actual deployed version.
        version_info = VersionInfo.objects.create(pk=VersionInfo.singleton_instance_id)

    code_version = get_current_version()
    if code_version in (
        VERSION_UNKNOWN,
        VERSION_LATEST,
        VERSION_DEV,
        settings.GIT_SHA,
    ):
        # this is normal in development
        if settings.DEBUG:
            return []

        return [
            Warning(
                f"Current code version was determined as '{code_version}', which prevents "
                "us from checking your upgrade path. Proceed at your own risk.",
                hint="We recommend only upgrading to tagged releases.",
                id="upgrades.W001",
            )
        ]

    recorded_version = version_info.current
    if recorded_version == code_version:
        return []

    try:
        if check_upgrade_path(recorded_version, code_version):
            return []
    except VersionParseError as err:
        return [
            Warning(
                f"Could not parse '{err.args[0]}' as a "
                "version number which prevents us from checking your upgrade path. "
                "Proceed at your own risk.",
                hint="We recommend only upgrading from and to tagged releases.",
                id="upgrades.W002",
            )
        ]

    return [
        Error(
            f"Upgrading (directly) to '{code_version}' from '{recorded_version}' "
            "is not supported.",
            hint="Consult the release notes for upgrade instructions",
            id="upgrades.E001",
        )
    ]
