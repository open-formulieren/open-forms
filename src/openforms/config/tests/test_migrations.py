from django.utils.translation import gettext_lazy as _

from openforms.utils.tests.test_migrations import TestMigrations


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


class ConfigTemplatesMigrationTest(TestMigrations):
    app = "config"
    migrate_from = "0001_initial_squashed_0022_merge_20210903_1228"
    migrate_to = "0043_globalconfiguration_templates"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            submission_confirmation_template=_("Inzending ontvangen"),
            form_previous_text=_("Vorige stap"),
        )

    def test_config_templates(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()
        template = config.submission_confirmation_template
        template_nl = config.submission_confirmation_template_nl

        form_previous_text = config.form_previous_text
        form_previous_text_nl = config.form_previous_text_nl

        self.assertEqual(template_nl, template)
        self.assertEqual(form_previous_text_nl, form_previous_text)
