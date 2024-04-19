from openforms.utils.tests.test_migrations import TestMigrations


class UpdateSourceIDsGovMetricTests(TestMigrations):
    app = "analytics_tools"
    migrate_from = (
        "0007_alter_analyticstoolsconfiguration_analytics_cookie_consent_group"
    )
    migrate_to = (
        "0010_remove_analyticstoolsconfiguration_govmetric_secure_guid_and_more"
    )

    def setUpBeforeMigration(self, apps):
        AnalyticsToolsConfiguration = apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )
        AnalyticsToolsConfiguration.objects.create(
            govmetric_source_id_en="1234",
            govmetric_source_id_nl="7890",
            govmetric_secure_guid_en="4321",
            govmetric_secure_guid_nl="0987",
        )

    def test_forward_migration(self):
        AnalyticsToolsConfiguration = self.apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )
        config = AnalyticsToolsConfiguration.objects.get()

        self.assertEqual(config.govmetric_source_id_form_aborted_en, "1234")
        self.assertEqual(config.govmetric_source_id_form_aborted_nl, "7890")
        self.assertEqual(config.govmetric_source_id_form_finished_en, "1234")
        self.assertEqual(config.govmetric_source_id_form_finished_nl, "7890")

        self.assertEqual(config.govmetric_secure_guid_form_aborted_en, "4321")
        self.assertEqual(config.govmetric_secure_guid_form_aborted_nl, "0987")
        self.assertEqual(config.govmetric_secure_guid_form_finished_en, "4321")
        self.assertEqual(config.govmetric_secure_guid_form_finished_nl, "0987")


class UndoUpdateSourceIDsGovMetricTests(TestMigrations):
    app = "analytics_tools"
    migrate_to = "0007_alter_analyticstoolsconfiguration_analytics_cookie_consent_group"
    migrate_from = (
        "0010_remove_analyticstoolsconfiguration_govmetric_secure_guid_and_more"
    )

    def setUpBeforeMigration(self, apps):
        AnalyticsToolsConfiguration = apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )
        AnalyticsToolsConfiguration.objects.create(
            govmetric_source_id_form_aborted_en="1111",
            govmetric_source_id_form_aborted_nl="2222",
            govmetric_source_id_form_finished_en="3333",
            govmetric_source_id_form_finished_nl="4444",
            govmetric_secure_guid_form_aborted_en="5555",
            govmetric_secure_guid_form_aborted_nl="6666",
            govmetric_secure_guid_form_finished_en="7777",
            govmetric_secure_guid_form_finished_nl="8888",
        )

    def test_backward_migration(self):
        AnalyticsToolsConfiguration = self.apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )
        config = AnalyticsToolsConfiguration.objects.get()

        self.assertEqual(config.govmetric_source_id_en, "3333")
        self.assertEqual(config.govmetric_source_id_nl, "4444")

        self.assertEqual(config.govmetric_secure_guid_en, "7777")
        self.assertEqual(config.govmetric_secure_guid_nl, "8888")
