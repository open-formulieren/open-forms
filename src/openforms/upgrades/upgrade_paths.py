import contextlib
import sys
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.core.management import CommandError, call_command
from django.utils.module_loading import import_string

import structlog
from semantic_version import SimpleSpec, Version

from .models import VERSION_DEV

__all__ = ["check_upgrade_path"]

logger = structlog.stdlib.get_logger(__name__)


class VersionParseError(Exception):
    pass


@dataclass(frozen=True)
class VersionRange:
    minimum: str
    maximum: str = ""

    def contains(self, in_version: Version):
        min_version = Version.coerce(self.minimum)
        max_version = Version.coerce(self.maximum) if self.maximum else None
        if in_version < min_version:
            return False
        if max_version and in_version > max_version:
            return False
        return True


@dataclass(frozen=True)
class UpgradeConstraint:
    """
    Encode constraints to upgrade to a particular version.

    This consists of allowed version ranges you can upgrade from, but also
    any scripts and/or management commands to need to complete succesfully
    before you can upgrade.
    """

    valid_ranges: Collection[VersionRange]
    management_commands: Collection[str] = field(default_factory=list)
    scripts: Collection[str] = field(default_factory=list)

    def run_checks(self) -> bool:
        checks_pass = True
        for command in self.management_commands:
            try:
                call_command(command)
            except CommandError:
                checks_pass = False

        for script in self.scripts:
            main_func = import_string(f"{script}.main")
            try:
                result = main_func(skip_setup=True)
            except Exception as exc:
                logger.error("script_check_error", exc_info=exc)
                result = False
            if result is False:
                checks_pass = False

        return checks_pass


# Mapping of version to upgrade to with a collection of supported version ranges.
# If your current version falls outside of a supported range, you need to do another
# upgrade path (first) or there is no upgrade path at all.
UPGRADE_PATHS = {
    "3.1": UpgradeConstraint(
        valid_ranges={VersionRange(minimum="3.0.1")},
    ),
    "3.3": UpgradeConstraint(
        valid_ranges={
            VersionRange(minimum="3.1.7", maximum="3.2.0"),
            VersionRange(minimum="3.2.2", maximum="3.3.0"),
        },
        scripts=["report_duplicate_merchants"],
    ),
}


@contextlib.contextmanager
def setup_scripts_env():
    """
    Set up the python path for the script execution, if any.

    Since the scripts in the ``bin`` dir are self-contained, we need to add the path
    to the python path to dynamically import the ``main`` function from the scripts.
    """
    bin_dir = str(Path(settings.BASE_DIR) / "bin")
    sys.path.insert(0, bin_dir)
    try:
        yield
    finally:
        sys.path.remove(bin_dir)


def check_upgrade_path(from_version: str, to_version: str) -> bool:
    # if you're in dev mode, you are definitely responsible for checking the migrations
    # etc. yourself.
    if to_version == VERSION_DEV:
        return True

    # find the most appropriate constraint
    try:
        _to_version = Version.coerce(to_version).truncate()
    except ValueError as exc:
        raise VersionParseError(to_version) from exc

    target_version = None
    for target_version, upgrade_constraint in UPGRADE_PATHS.items():  # noqa: B007
        # 1. start by trying an exact match, which always wins
        if target_version == to_version:
            break

        # 2. Check the ~=X.Y.x version range, which allows the major.minor range. E.g.
        # 2.0.1 matches ~= 2.0.0, but 2.1.0 does not.
        compare_spec = SimpleSpec(f"~={target_version}")
        if _to_version in compare_spec:
            break
    # we did not find a match, this means there are no (known) upgrade constraints for
    # the new version, or you are supposed to know what you're doing.
    else:
        return True

    # check if we have a semver-like current/from version
    try:
        in_version = Version(from_version)
    except ValueError as exc:
        raise VersionParseError(from_version) from exc

    # handles the case where there's a check for 2.0 coming from < 2.0, but skip the
    # checks if you're on 2.0.1 or something like that.
    if target_version:
        compare_spec = SimpleSpec(f"~={target_version}")
        if in_version in compare_spec:
            return True

    if not any(
        version_range.contains(in_version)
        for version_range in upgrade_constraint.valid_ranges
    ):
        return False

    with setup_scripts_env():
        return upgrade_constraint.run_checks()
