from django.test import override_settings

from openforms.utils.tests.test_migrations import TestMigrations

from ..models import GlobalConfiguration


@override_settings(SOLO_CACHE=None)
class DesignTokenMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0028_auto_20220601_1422"
    migrate_to = "0029_rename_design_tokens"

    def setUpBeforeMigration(self, apps):
        config = GlobalConfiguration.get_solo()
        config.design_token_values = {
            "unrelated": {"token": {"value": "foo"}},
            "color": {"link": {"value": "white"}},
        }
        config.save()

    def test_no_global_config_instance_exists(self):
        config = GlobalConfiguration.get_solo()

        expected = {
            "unrelated": {"token": {"value": "foo"}},
            "link": {"color": {"value": "white"}},
        }
        self.assertEqual(config.design_token_values, expected)
