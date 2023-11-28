from django.contrib.admin.options import get_content_type_for_model
from django.db.migrations.state import StateApps

from openforms.analytics_tools.constants import AnalyticsTools
from openforms.config.constants import CSPDirective
from openforms.utils.tests.test_migrations import TestMigrations


class CSPSettingIdentifierMigrationTests(TestMigrations):
    app = "analytics_tools"
    migrate_from = "0002_auto_20230119_1500"
    migrate_to = "0003_cspsetting_identifier"

    def setUpBeforeMigration(self, apps: StateApps):
        CSPSetting = apps.get_model("config", "CSPSetting")
        AnalyticsToolsConfiguration = apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )

        AnalyticsToolsConfiguration.objects.create(
            matomo_url="https://matomo.example.com",
            piwik_url="https://piwik.example.com",
            piwik_pro_url="https://your-instance-name.piwik.pro",
        )

        CSPSetting.objects.create(
            directive=CSPDirective.DEFAULT_SRC, value="https://matomo.example.com"
        )
        CSPSetting.objects.create(
            directive=CSPDirective.DEFAULT_SRC, value="https://piwik.example.com"
        )
        CSPSetting.objects.create(
            directive=CSPDirective.DEFAULT_SRC,
            value="https://your-instance-name.piwik.pro",
        )
        CSPSetting.objects.create(
            directive=CSPDirective.DEFAULT_SRC, value="https://siteimproveanalytics.com"
        )
        CSPSetting.objects.create(
            directive=CSPDirective.DEFAULT_SRC, value="https://www.googleanalytics.com"
        )

    def test_migration_sets_identifier_and_gfk(self):
        CSPSetting = self.apps.get_model("config", "CSPSetting")
        AnalyticsToolsConfiguration = self.apps.get_model(
            "analytics_tools", "AnalyticsToolsConfiguration"
        )
        analytics_conf = AnalyticsToolsConfiguration.objects.get()

        value_to_identifier = {
            "https://matomo.example.com": AnalyticsTools.matomo,
            "https://piwik.example.com": AnalyticsTools.piwik,
            "https://your-instance-name.piwik.pro": AnalyticsTools.piwik_pro,
            "https://siteimproveanalytics.com": AnalyticsTools.siteimprove,
            "https://www.googleanalytics.com": AnalyticsTools.google_analytics,
        }

        self.assertFalse(CSPSetting.objects.filter(identifier="").exists())
        
        # We avoid using django.contrib.admin.options.get_content_type_for_model
        # as it uses the "real" `ContentType` model. See:
        # https://stackoverflow.com/q/51670468/#comment110467392_54357872
        content_type = self.apps.get_model(
            "contenttypes", "ContentType"
        ).objects.get_for_model(analytics_conf)

        for value, identifier in value_to_identifier.items():
            self.assertEqual(
                CSPSetting.objects.filter(
                    value=value,
                    identifier=identifier,
                    content_type=content_type,
                    object_id=str(analytics_conf.pk),
                ).count(),
                1,
            )
