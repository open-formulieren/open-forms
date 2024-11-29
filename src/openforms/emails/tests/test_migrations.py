from textwrap import dedent

from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class MigrateSummaryTag(TestMigrations):
    app = "emails"
    migrate_from = "0002_confirmationemailtemplate_cosign_content_and_more"
    migrate_to = "0003_update_summary_tags"

    def setUpBeforeMigration(self, apps: StateApps):
        Form = apps.get_model("forms", "Form")
        ConfirmationEmailTemplate = apps.get_model(
            "emails", "ConfirmationEmailTemplate"
        )

        form1 = Form.objects.create(name="test 1")
        form2 = Form.objects.create(name="test 2")

        test_template = dedent(
            r"""
            Some prefix
            {% summary %}
            {%summary%}
            {%   summary%}
            {%summary  %}
            {% other_tag %}
        """
        )

        ConfirmationEmailTemplate.objects.create(
            form=form1,
            content_nl=test_template,
            content_en=r"Leave {% summar %}{% y %}untouched",
        )
        ConfirmationEmailTemplate.objects.create(
            form=form2,
            cosign_content_nl=test_template,
            content_en=r"Leave {% confirmation_summary %} untouched",
        )

    def test_content_migrated(self):
        ConfirmationEmailTemplate = self.apps.get_model(
            "emails", "ConfirmationEmailTemplate"
        )

        with self.subTest("templates form 1"):
            tpl1 = ConfirmationEmailTemplate.objects.get(form__name="test 1")

            expected = dedent(
                r"""
                Some prefix
                {% confirmation_summary %}
                {% confirmation_summary %}
                {% confirmation_summary %}
                {% confirmation_summary %}
                {% other_tag %}
            """
            )
            self.assertEqual(tpl1.content_nl, expected)
            self.assertEqual(tpl1.content_en, r"Leave {% summar %}{% y %}untouched")

        with self.subTest("templates form 2"):
            tpl2 = ConfirmationEmailTemplate.objects.get(form__name="test 2")

            expected = dedent(
                r"""
                Some prefix
                {% summary %}
                {%summary%}
                {%   summary%}
                {%summary  %}
                {% other_tag %}
            """
            )
            self.assertEqual(tpl2.cosign_content_nl, expected)
            self.assertEqual(
                tpl2.content_en, r"Leave {% confirmation_summary %} untouched"
            )
