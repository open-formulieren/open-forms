from django.test import SimpleTestCase, TestCase, override_settings

from ..models import VersionInfo
from ..signals import update_current_version


class VersionInfoTests(SimpleTestCase):
    @override_settings(LANGUAGE_CODE="en")
    def test_string_representation(self):
        version_info = VersionInfo()

        self.assertEqual(str(version_info), "version information")

    def test_current_version_from_release(self):
        for release in (
            "latest",
            "1.0.0",
            "2.0.0-beta.0",
            "0b5b0c04ff322bf098872081319decfe558c9f73",
        ):
            with self.subTest(release=release):
                with override_settings(RELEASE=release):
                    version_info = VersionInfo()

                    self.assertEqual(version_info.current, release)

    @override_settings(RELEASE=None, GIT_SHA="0b5b0c04ff322bf098872081319decfe558c9f73")
    def test_fallback_to_git_sha(self):
        version_info = VersionInfo()

        self.assertEqual(
            version_info.current, "0b5b0c04ff322bf098872081319decfe558c9f73"
        )

    @override_settings(RELEASE=None, GIT_SHA=None)
    def test_fallback_to_unknown(self):
        version_info = VersionInfo()

        self.assertEqual(version_info.current, "UNKNOWN")


class VersionInfoDatabaseTests(TestCase):
    def test_cache_disabled(self):
        VersionInfo.get_solo()
        VersionInfo.objects.update(current="updated-version")

        version_info = VersionInfo.get_solo()

        self.assertEqual(version_info.current, "updated-version")

    def test_post_migrate_signal(self):
        VersionInfo.objects.update(git_sha="e13f0d277159541bd2c34e1d026c23170bb03ca9")
        VersionInfo.get_solo()

        with override_settings(
            RELEASE="newer", GIT_SHA="0b5b0c04ff322bf098872081319decfe558c9f73"
        ):
            update_current_version(self)

        version_info = VersionInfo.get_solo()
        self.assertEqual(version_info.current, "newer")
        self.assertEqual(
            version_info.git_sha, "0b5b0c04ff322bf098872081319decfe558c9f73"
        )
