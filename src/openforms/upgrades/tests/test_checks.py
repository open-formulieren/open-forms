from unittest.mock import patch

from django.core.checks import Error, Warning
from django.db import OperationalError, ProgrammingError
from django.test import TestCase, override_settings

from ..checks import check_upgrade_possible
from ..models import VersionInfo
from ..upgrade_paths import UpgradeConstraint, VersionRange
from .utils import mock_upgrade_paths


def mock_version_info(**kwargs):
    return patch("openforms.upgrades.checks.get_version_info", **kwargs)


def mock_upgrade_path_possible(possible: bool):
    return patch("openforms.upgrades.checks.check_upgrade_path", return_value=possible)


class DatabaseNotInitializedUpgradeCheckTests(TestCase):
    """
    If the database is not initialized, checks may not block this initialization.
    """

    @mock_version_info(side_effect=OperationalError)
    def test_db_connection_fails(self, *mocks):
        errors_and_warnings = check_upgrade_possible(None)

        self.assertEqual(errors_and_warnings, [])

    @mock_version_info(side_effect=ProgrammingError)
    def test_db_query_fails(self, *mocks):
        errors_and_warnings = check_upgrade_possible(None)

        self.assertEqual(errors_and_warnings, [])

    @override_settings(RELEASE="unit-tests")
    def test_create_initial_information(self):
        # delete any instances that may exist
        VersionInfo.get_solo().delete()

        errors_and_warnings = check_upgrade_possible(None)

        self.assertEqual(errors_and_warnings, [])
        version_info = VersionInfo.objects.get()
        self.assertEqual(version_info.current, "unit-tests")


class UpgradeCheckTests(TestCase):
    @override_settings(DEBUG=True, RELEASE="latest")
    def test_development_mode_with_release(self):
        for version in ("latest", "68952f07ae778ae0f6879c9e1b290dc33f4b1aad"):
            with self.subTest(current_version=version):
                with mock_version_info(return_value=VersionInfo(current=version)):
                    errors_and_warnings = check_upgrade_possible(None)

                    self.assertEqual(errors_and_warnings, [])

    @override_settings(
        DEBUG=True,
        RELEASE="e13f0d277159541bd2c34e1d026c23170bb03ca9",
        GIT_SHA="e13f0d277159541bd2c34e1d026c23170bb03ca9",
    )
    def test_development_mode_inferred_git_hash(self):
        for version in ("latest", "68952f07ae778ae0f6879c9e1b290dc33f4b1aad"):
            with self.subTest(current_version=version):
                with mock_version_info(return_value=VersionInfo(current=version)):
                    errors_and_warnings = check_upgrade_possible(None)

                    self.assertEqual(errors_and_warnings, [])

    @override_settings(RELEASE=None, GIT_SHA=None)
    def test_no_release_or_git_sha(self):
        with self.subTest(debug=True):
            with override_settings(DEBUG=True):
                errors_and_warnings = check_upgrade_possible(None)

                self.assertEqual(errors_and_warnings, [])

        with self.subTest(debug=False):
            with override_settings(DEBUG=False):
                errors_and_warnings = check_upgrade_possible(None)

                warning = Warning(
                    "Current code version was determined as 'UNKNOWN', which prevents "
                    "us from checking your upgrade path. Proceed at your own risk.",
                    hint="We recommend only upgrading to tagged releases.",
                    id="upgrades.W001",
                )
                self.assertEqual(errors_and_warnings, [warning])

    @override_settings(RELEASE="2.0.0-beta.1")
    def test_cannot_parse_current_version(self):
        UPGRADE_PATHS = {
            "2.0": UpgradeConstraint(valid_ranges={VersionRange(minimum="1.1")}),
        }
        version_info = VersionInfo(current="68952f07ae778ae0f6879c9e1b290dc33f4b1aad")

        with mock_upgrade_paths(UPGRADE_PATHS), mock_version_info(
            return_value=version_info
        ):
            errors_and_warnings = check_upgrade_possible(None)

            warning = Warning(
                "Could not parse '68952f07ae778ae0f6879c9e1b290dc33f4b1aad' as a "
                "version number which prevents us from checking your upgrade path. "
                "Proceed at your own risk.",
                hint="We recommend only upgrading from and to tagged releases.",
                id="upgrades.W002",
            )
            self.assertEqual(errors_and_warnings, [warning])

    @override_settings(RELEASE="newer")
    def test_upgrade_path_allowed(self):
        with mock_version_info(return_value=VersionInfo(current="older")):
            with mock_upgrade_path_possible(True) as mock_check:
                errors_and_warnings = check_upgrade_possible(None)

                self.assertEqual(errors_and_warnings, [])
                mock_check.assert_called_once_with("older", "newer")

    @override_settings(RELEASE="some-experimental-tag", DEBUG=False)
    def test_non_numeric_release_tag(self):
        with mock_version_info(return_value=VersionInfo(current="2.0.0")):
            errors_and_warnings = check_upgrade_possible(None)

            warning = Warning(
                "Could not parse 'some-experimental-tag' as a version number which "
                "prevents us from checking your upgrade path. Proceed at your own risk.",
                hint="We recommend only upgrading from and to tagged releases.",
                id="upgrades.W002",
            )
            self.assertEqual(errors_and_warnings, [warning])

    @override_settings(RELEASE="newer")
    def test_upgrade_path_not_allowed(self):
        with mock_version_info(return_value=VersionInfo(current="older")):
            with mock_upgrade_path_possible(False) as mock_check:
                errors_and_warnings = check_upgrade_possible(None)

                error = Error(
                    "Upgrading (directly) to 'newer' from 'older' is not supported.",
                    hint="Consult the release notes for upgrade instructions",
                    id="upgrades.E001",
                )
                self.assertEqual(errors_and_warnings, [error])
                mock_check.assert_called_once_with("older", "newer")
