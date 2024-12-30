from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class MigrateSummaryTag(TestMigrations):
    app = "config"
    migrate_from = "0054_v250_to_v270"
    migrate_to = "0055_v270_to_v300"

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
