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


@override_settings(SOLO_CACHE=None)
class AddPrefixDesignTokenMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0034_alter_globalconfiguration_form_upload_default_file_types"
    migrate_to = "0035_update_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            design_token_values={
                "prop1": {"prop2": {"value": "foo"}},
                "prop3": {"prop4": {"value": "white"}},
            }
        )

    def test_design_tokens_updated(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()
        expected = {
            "of": {
                "prop1": {"prop2": {"value": "foo"}},
                "prop3": {"prop4": {"value": "white"}},
            }
        }

        self.assertEqual(config.design_token_values, expected)


@override_settings(SOLO_CACHE=None)
class AddPrefixDesignTokenMigrationNoTokensTests(TestMigrations):
    app = "config"
    migrate_from = "0034_alter_globalconfiguration_form_upload_default_file_types"
    migrate_to = "0035_update_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create()

    def test_design_tokens_updated(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertEqual(config.design_token_values, {})


@override_settings(SOLO_CACHE=None)
class AddPrefixDesignTokenMigrationRenameLinkPropertiesTests(TestMigrations):
    app = "config"
    migrate_from = "0034_alter_globalconfiguration_form_upload_default_file_types"
    migrate_to = "0035_update_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            design_token_values={
                "link": {
                    "color": {"value": "foo"},
                    "hover": {"color": {"value": "bar"}},
                },
                "prop3": {"prop4": {"value": "white"}},
            }
        )

    def test_design_tokens_updated(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()
        expected = {
            "of": {"prop3": {"prop4": {"value": "white"}}},
            "utrecht": {
                "link": {
                    "color": {"value": "foo"},
                    "hover": {"color": {"value": "bar"}},
                }
            },
        }

        self.assertEqual(config.design_token_values, expected)


@override_settings(SOLO_CACHE=None)
class RemovePrefixDesignTokenMigrationRenameLinkPropertiesTests(TestMigrations):
    app = "config"
    migrate_to = "0034_alter_globalconfiguration_form_upload_default_file_types"
    migrate_from = "0035_update_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            design_token_values={
                "utrecht": {
                    "link": {
                        "color": {"value": "foo"},
                        "hover": {"color": {"value": "bar"}},
                    }
                },
                "of": {"prop3": {"prop4": {"value": "white"}}},
                "other-theme": {"prop5": {"value": "blue"}},
            }
        )

    def test_design_tokens_updated(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()
        expected = {
            "prop3": {"prop4": {"value": "white"}},
            "link": {
                "color": {"value": "foo"},
                "hover": {"color": {"value": "bar"}},
            },
        }

        self.assertEqual(config.design_token_values, expected)
