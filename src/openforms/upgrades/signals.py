from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import VersionInfo, get_current_version, get_default_git_sha


@receiver(post_migrate, dispatch_uid="upgrades_update_current_version")
def update_current_version(sender, **kwargs):
    version_info = VersionInfo.get_solo()
    current_version = get_current_version()
    current_git_sha = get_default_git_sha()

    update_fields = []
    if version_info.current != current_version:
        update_fields.append("current")
        version_info.current = current_version
    if version_info.git_sha != current_git_sha:
        update_fields.append("git_sha")
        version_info.git_sha = current_git_sha

    if update_fields:
        version_info.save(update_fields=update_fields)
