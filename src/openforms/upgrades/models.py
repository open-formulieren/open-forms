from django.conf import settings
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

VERSION_UNKNOWN = "UNKNOWN"
VERSION_LATEST = "latest"
VERSION_DEV = "dev"


def get_current_version() -> str:
    release = settings.RELEASE
    return release or settings.GIT_SHA or VERSION_UNKNOWN


def get_default_git_sha() -> str:
    return settings.GIT_SHA or VERSION_UNKNOWN


class VersionInfo(SingletonModel):
    current = models.CharField(
        _("current version"),
        max_length=100,
        editable=False,
        default=get_current_version,
    )
    git_sha = models.CharField(
        _("current git hash"),
        max_length=100,
        editable=False,
        default=get_default_git_sha,
    )

    class Meta:
        verbose_name = _("version information")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    def set_to_cache(self):
        """
        Disable solo caching for this model.

        We always want to get the value from the database for version information
        introspection.
        """
        pass
