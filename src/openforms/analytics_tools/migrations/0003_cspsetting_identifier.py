# Generated by Django 3.2.21 on 2023-11-22 17:27

from django.db import migrations
from django.db.migrations.state import StateApps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from openforms.analytics_tools.constants import AnalyticsTools

SITEIMPROVE_VALUES = [
    "https://siteimproveanalytics.com",
    "https://siteimproveanalytics.com",
    "https://*.siteimproveanalytics.io",
]
GA_VALUES = ["https://www.googleanalytics.com", "https://www.googletagmanager.com"]

FIELD_TO_IDENTIFIER = {
    "matomo_url": AnalyticsTools.matomo,
    "piwik_pro_url": AnalyticsTools.piwik_pro,
    "piwik_url": AnalyticsTools.piwik,
}


def set_identifier(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Set the corresponding analytic tool as the ``CSPSetting.identifier`` field.

    Depending on the analytic tool used, the ``CSPSetting.value`` field can be fixed
    (e.g. with GA or Siteimprove) or configured by the user. The latter requires more work,
    as we need to iterate over the ``AnalyticsToolsConfiguration`` fields to find the right match.
    """

    AnalyticsToolsConfiguration = apps.get_model(
        "analytics_tools", "AnalyticsToolsConfiguration"
    )
    analytics_conf = AnalyticsToolsConfiguration.get_solo()
    CSPSetting = apps.get_model("config", "CSPSetting")

    for csp_setting in CSPSetting.objects.filter(identifier="").iterator():
        if csp_setting.value in SITEIMPROVE_VALUES:
            csp_setting.identifier = AnalyticsTools.siteimprove
        elif csp_setting.value in GA_VALUES:
            csp_setting.identifier = AnalyticsTools.google_analytics
        else:
            for field, identifier in FIELD_TO_IDENTIFIER.items():
                if getattr(analytics_conf, field) == csp_setting.value:
                    csp_setting.identifier = identifier

        csp_setting.save()


class Migration(migrations.Migration):

    dependencies = [
        ("analytics_tools", "0002_auto_20230119_1500"),
    ]

    operations = [
        migrations.RunPython(set_identifier, migrations.RunPython.noop),
    ]
