from django.test import override_settings
from django.utils.translation import gettext_lazy as _

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


@override_settings(SOLO_CACHE=None)
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


@override_settings(SOLO_CACHE=None)
class ConfirmationEmailTemplatesCosignTest(TestMigrations):
    app = "config"
    migrate_from = "0047_globalconfiguration_enable_new_appointments"
    migrate_to = "0048_add_cosign_templatetag"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(
            confirmation_email_content="""
            Dear Sir, Madam,<br>
            You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
            Your reference is: {{ public_reference }}<br>

            {% summary %}<br>
            {% appointment_information %}<br>
            {% payment_information %}<br><br>

            Kind regards,<br>
            <br>
            Open Forms<br>
            """
        )

    def test_template_after_migration_contains_cosign_tag(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")

        config = GlobalConfiguration.objects.get()

        self.assertIn("{% cosign_information %}", config.confirmation_email_content)
        self.assertIn("{% summary %}", config.confirmation_email_content)
        self.assertIn(
            "{% appointment_information %}", config.confirmation_email_content
        )

        self.assertIn("{% cosign_information %}", config.confirmation_email_content_nl)
        self.assertIn("{% summary %}", config.confirmation_email_content_nl)
        self.assertIn(
            "{% appointment_information %}", config.confirmation_email_content_nl
        )

        self.assertIn("{% cosign_information %}", config.confirmation_email_content_en)
        self.assertIn("{% summary %}", config.confirmation_email_content_en)
        self.assertIn(
            "{% appointment_information %}", config.confirmation_email_content_en
        )
