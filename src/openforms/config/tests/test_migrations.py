from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class MigrateFeatureFlagsTests(TestMigrations):
    app = "config"
    migrate_from = "0001_initial_to_v250"
    migrate_to = "0054_v250_to_v270"

    def setUpBeforeMigration(self, apps: StateApps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.update_or_create(
            pk=1,
            defaults={
                "enable_demo_plugins": True,
                "display_sdk_information": False,
            },
        )
        FlagState = apps.get_model("flags", "FlagState")
        FlagState.objects.all().delete()

    def test_feature_flags_created(self):
        FlagState = self.apps.get_model("flags", "FlagState")
        flags = FlagState.objects.all()

        self.assertEqual(len(flags), 2)
        by_name = {flag.name: flag for flag in flags}

        flag1 = by_name["ENABLE_DEMO_PLUGINS"]
        self.assertEqual(flag1.condition, "boolean")
        self.assertEqual(flag1.value, "True")

        flag2 = by_name["DISPLAY_SDK_INFORMATION"]
        self.assertEqual(flag2.condition, "boolean")
        self.assertEqual(flag2.value, "False")


class ReverseMigrateFeatureFlagsTests(TestMigrations):
    app = "config"
    migrate_from = "0054_v250_to_v270"
    migrate_to = "0001_initial_to_v250"

    def setUpBeforeMigration(self, apps: StateApps):
        FlagState = apps.get_model("flags", "FlagState")
        FlagState.objects.all().delete()
        FlagState.objects.create(
            name="ENABLE_DEMO_PLUGINS", condition="boolean", value="yes"
        )
        FlagState.objects.create(
            name="UNRELATED", condition="invalid", value="irrelevant"
        )

        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.get_or_create(pk=1)

    def test_feature_flags_created(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertTrue(config.enable_demo_plugins)
        self.assertFalse(config.display_sdk_information)


class MigrateSummaryTag(TestMigrations):
    app = "config"
    migrate_from = "0068_alter_globalconfiguration_cosign_request_template_and_more"
    migrate_to = "0068_update_summary_tags"

    def setUpBeforeMigration(self, apps: StateApps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        test_template = r"""
            Some prefix
            {% summary %}
            {%summary%}
            {%   summary%}
            {% summary  %}
            {% other_tag %}
        """
        GlobalConfiguration.objects.update_or_create(
            pk=1,
            defaults={
                "submission_confirmation_template_nl": test_template,
                "submission_confirmation_template_en": test_template,
                "confirmation_email_content_nl": test_template,
                "confirmation_email_content_en": test_template,
            },
        )

    def test_content_migrated(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        expected = r"""
            Some prefix
            {% confirmation_summary %}
            {% confirmation_summary %}
            {% confirmation_summary %}
            {% confirmation_summary %}
            {% other_tag %}
        """
        for field in (
            "submission_confirmation_template_nl",
            "submission_confirmation_template_en",
            "confirmation_email_content_nl",
            "confirmation_email_content_en",
        ):
            with self.subTest(field=field):
                result = getattr(config, field)

                self.assertEqual(result, expected)
