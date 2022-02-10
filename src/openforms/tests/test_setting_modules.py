from importlib import import_module

from django.test import SimpleTestCase

ENVS = [
    "dev",
    "ci",
    "test",
    "staging",
    "production",
    "docker",
]


class SettingModuleImportTests(SimpleTestCase):
    """
    Test that the setting modules can be imported without errors.
    """

    def test_can_import_setting_modules(self):
        for env in ENVS:
            with self.subTest(env=env):
                module = f"openforms.conf.{env}"

                import_module(module)
