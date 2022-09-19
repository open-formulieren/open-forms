from django.test import override_settings

from openforms.utils.tests.test_migrations import TestMigrations


@override_settings(SOLO_CACHE=None)
class DesignTokenMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0002_make_react_ui_default_squashed_0028_auto_20220601_1422"
    migrate_to = "0029_rename_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        self.config = GlobalConfiguration.objects.create(
            design_token_values={
                "unrelated": {"token": {"value": "foo"}},
                "color": {"link": {"value": "white"}},
            }
        )

    def test_no_global_config_instance_exists(self):
        self.config.refresh_from_db()
        expected = {
            "unrelated": {"token": {"value": "foo"}},
            "link": {"color": {"value": "white"}},
        }
        self.assertEqual(self.config.design_token_values, expected)


@override_settings(SOLO_CACHE=None)
class EmptyDesignTokenMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0002_make_react_ui_default_squashed_0028_auto_20220601_1422"
    migrate_to = "0029_rename_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        self.config = GlobalConfiguration.objects.create(design_token_values={})

    def test_empty_design_token_values(self):
        self.config.refresh_from_db()
        self.assertEqual(self.config.design_token_values, {})
