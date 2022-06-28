from django.db import connection
from django.test import override_settings

from openforms.utils.tests.test_migrations import TestMigrations

from ..models import GlobalConfiguration


class GlobalConfigurationTestMigration(TestMigrations):
    app = "config"

    # fmt: off
    CONFIG_INSERT_SQL = """
    INSERT INTO "config_globalconfiguration" ("id", "email_template_netloc_allowlist", "submission_confirmation_template", "confirmation_email_subject", "confirmation_email_content", "allow_empty_initiator", "form_previous_text", "form_change_text", "form_confirm_text", "form_begin_text", "form_step_previous_text", "form_step_save_text", "form_step_next_text", "form_fields_required_default", "form_display_required_with_asterisk", "logo", "main_website", "design_token_values", "theme_classname", "theme_stylesheet", "admin_session_timeout", "form_session_timeout", "payment_order_id_prefix", "gtm_code", "ga_code", "matomo_url", "matomo_site_id", "piwik_url", "piwik_site_id", "siteimprove_id", "analytics_cookie_consent_group_id", "ask_privacy_consent", "privacy_policy_url", "privacy_policy_label", "enable_demo_plugins", "default_test_bsn", "default_test_kvk", "display_sdk_information", "successful_submissions_removal_limit", "successful_submissions_removal_method", "incomplete_submissions_removal_limit", "incomplete_submissions_removal_method", "errored_submissions_removal_limit", "errored_submissions_removal_method", "all_submissions_removal_limit", "registration_attempt_limit", "plugin_configuration", "enable_form_variables") VALUES (%s, %s::varchar(1000)[], %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING "config_globalconfiguration"."id"
    """
    CONFIG_INSERT_ARGS = (1, [], 'Thank you for submitting this form.', 'Confirmation of your {{ form_name }} submission', '\n\n\n\n\n\n\nDear Sir, Madam,<br>\n<br>\nYou have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>\n<br>\nYour reference is: {{ public_reference }}<br>\n<br>\n\n{% summary %}<br>\n{% appointment_information %}<br>\n{% payment_information %}<br><br>\n\n<br>\nKind regards,<br>\n<br>\nOpen Forms<br>\n\n', False, 'Previous page', 'Wijzigen', 'Confirm', 'Begin form', 'Previous page', 'Save current information', 'Volgende', False, True, '', '', '{}', '', '', 60, 15, '{year}', '', '', '', None, '', None, '', None, True, '', 'Ja, ik heb kennis genomen van het {% privacy_policy %} en geef uitdrukkelijk toestemming voor het verwerken van de door mij opgegeven gegevens.', False, '', '', False, 7, 'delete_permanently', 7, 'delete_permanently', 30, 'delete_permanently', 90, 5, '{}', False)
    # fmt: on

    def _get_global_configuration(self):
        return GlobalConfiguration.objects.only("design_token_values").get()

    def setUpBeforeMigration(self, apps):
        with connection.cursor() as cursor:
            cursor.execute(self.CONFIG_INSERT_SQL, self.CONFIG_INSERT_ARGS)


@override_settings(SOLO_CACHE=None)
class DesignTokenMigrationTests(GlobalConfigurationTestMigration):
    migrate_from = "0028_auto_20220601_1422"
    migrate_to = "0029_rename_design_tokens"

    def setUpBeforeMigration(self, apps):
        super().setUpBeforeMigration(apps)
        config = self._get_global_configuration()
        config.design_token_values = {
            "unrelated": {"token": {"value": "foo"}},
            "color": {"link": {"value": "white"}},
        }
        config.save(update_fields=["design_token_values"])

    def test_no_global_config_instance_exists(self):
        config = self._get_global_configuration()
        expected = {
            "unrelated": {"token": {"value": "foo"}},
            "link": {"color": {"value": "white"}},
        }
        self.assertEqual(config.design_token_values, expected)


@override_settings(SOLO_CACHE=None)
    app = "config"
class EmptyDesignTokenMigrationTests(GlobalConfigurationTestMigration):
    migrate_from = "0028_auto_20220601_1422"
    migrate_to = "0029_rename_design_tokens"

    def setUpBeforeMigration(self, apps):
        super().setUpBeforeMigration(apps)
        config = self._get_global_configuration()
        config.design_token_values = {}
        config.save(update_fields=["design_token_values"])

    def test_empty_design_token_values(self):
        config = self._get_global_configuration()
        self.assertEqual(config.design_token_values, {})
