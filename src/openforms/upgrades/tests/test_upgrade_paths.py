import shutil
from pathlib import Path
from unittest import TestCase

from django.conf import settings
from django.test import SimpleTestCase

from ..upgrade_paths import (
    UpgradeConstraint,
    VersionParseError,
    VersionRange,
    check_upgrade_path,
)
from .utils import mock_upgrade_paths

FILES_DIR = (Path(__file__).parent / "files").resolve()


class UpgradePathTests(TestCase):
    def test_dev_mode(self):
        can_upgrade = check_upgrade_path("irrelevant", "dev")

        self.assertTrue(can_upgrade)

    def test_to_git_sha(self):
        # git hashes -> use at your own risk
        can_upgrade = check_upgrade_path(
            "irrelevant", "0b5b0c04ff322bf098872081319decfe558c9f73"
        )

        self.assertTrue(can_upgrade)

    def test_to_non_semver(self):
        # non-semver schemas aren't handled, if extensions use those, it's at their own risk
        can_upgrade = check_upgrade_path("irrelevant", "2022.03")

        self.assertTrue(can_upgrade)

    def test_semver_from_and_to(self):
        UPGRADE_PATHS = {
            "1.1.0": UpgradeConstraint(
                valid_ranges={
                    VersionRange(minimum="1.0.3"),
                    VersionRange(minimum="0.8.3", maximum="0.9.4"),
                }
            ),
            "2.0": UpgradeConstraint(
                valid_ranges={
                    VersionRange(minimum="1.1"),
                }
            ),
        }

        with mock_upgrade_paths(UPGRADE_PATHS):
            with self.subTest(from_version="1.0.4", to_version="1.1.0"):
                self.assertTrue(check_upgrade_path("1.0.4", "1.1.0"))

            with self.subTest(from_version="1.0.4", to_version="1.1.2"):
                self.assertTrue(check_upgrade_path("1.0.4", "1.1.2"))

            with self.subTest(from_version="0.8.4", to_version="1.1.1"):
                self.assertTrue(check_upgrade_path("0.8.4", "1.1.1"))

            with self.subTest(from_version="0.9.5", to_version="1.1.0"):
                self.assertFalse(check_upgrade_path("0.9.5", "1.1.0"))

            with self.subTest(from_version="1.1.5", to_version="2.1.0"):
                self.assertTrue(check_upgrade_path("1.1.5", "2.1.0"))

    def test_nonsemver_from_version(self):
        UPGRADE_PATHS = {
            "2.0": UpgradeConstraint(valid_ranges={VersionRange(minimum="1.1")})
        }

        with mock_upgrade_paths(UPGRADE_PATHS):
            with self.assertRaises(VersionParseError):
                check_upgrade_path("0b5b0c04ff322bf098872081319decfe558c9f73", "2.0")

    def test_already_on_target(self):
        """
        Assert that the checks are skipped if you are already on a version that matches
        the target version (2.0.1 matches ~2.0).
        """
        UPGRADE_PATHS = {
            "2.0": UpgradeConstraint(
                valid_ranges={
                    VersionRange(minimum="1.1"),
                },
                # throws exception if checks _are_ being executed
                scripts=["i-do-not-exist"],
            ),
        }
        with mock_upgrade_paths(UPGRADE_PATHS):
            with self.subTest(from_version="2.0.1", to="2.0.2"):
                self.assertTrue(check_upgrade_path("2.0.1", "2.0.2"))
            with self.subTest(from_version="2.0.1", to="2.1.2"):
                self.assertTrue(check_upgrade_path("2.0.1", "2.1.2"))


class DjangoScriptTests(SimpleTestCase):
    def test_check_management_commands(self):
        UPGRADE_PATHS = {
            "2.0.0": UpgradeConstraint(
                valid_ranges={VersionRange(minimum="1.1")},
                management_commands=["fail_upgrade_check"],
            )
        }

        with mock_upgrade_paths(UPGRADE_PATHS):
            self.assertFalse(check_upgrade_path("1.2.0", "2.0.0"))

    def test_check_script(self):
        script_dir = Path(settings.BASE_DIR) / "bin"

        UPGRADE_PATHS = {
            "2.0.0": UpgradeConstraint(
                valid_ranges={VersionRange(minimum="1.1")}, scripts=["check_pass"]
            ),
            "3.0.0": UpgradeConstraint(
                valid_ranges={VersionRange(minimum="2.0")}, scripts=["check_fail"]
            ),
            "4.0.0": UpgradeConstraint(
                valid_ranges={VersionRange(minimum="3.0")}, scripts=["check_error"]
            ),
        }

        for script in ("check_pass.py-tpl", "check_fail.py-tpl", "check_error.py-tpl"):
            src = FILES_DIR / script
            dest = script_dir / script.replace("-tpl", "")
            shutil.copyfile(src, dest)
            self.addCleanup(dest.unlink)

        with mock_upgrade_paths(UPGRADE_PATHS):
            with self.subTest("script check passes"):
                can_upgrade = check_upgrade_path("1.2.0", "2.0.0")

                self.assertTrue(can_upgrade)

            with self.subTest("script check fails"):
                can_upgrade = check_upgrade_path("2.2.0", "3.0.0")

                self.assertFalse(can_upgrade)

            with self.subTest("script check fails"):
                can_upgrade = check_upgrade_path("3.2.0", "4.0.0")

                self.assertFalse(can_upgrade)
