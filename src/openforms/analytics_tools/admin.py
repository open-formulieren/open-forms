from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from openforms.analytics_tools.models import AnalyticsToolsConfiguration


@admin.register(AnalyticsToolsConfiguration)
class AnalyticsToolsConfigurationAdmin(SingletonModelAdmin):
    autocomplete_fields = ("analytics_cookie_consent_group",)
    fieldsets = (
        (_("Analytics cookies group"), {"fields": ("analytics_cookie_consent_group",)}),
        (
            _("Analytics: Google"),
            {
                "fields": ("gtm_code", "ga_code", "enable_google_analytics"),
            },
        ),
        (
            _("Analytics: Matomo"),
            {
                "fields": (
                    "matomo_url",
                    "matomo_site_id",
                    "enable_matomo_site_analytics",
                ),
            },
        ),
        (
            _("Analytics: SiteImprove"),
            {
                "fields": ("siteimprove_id", "enable_siteimprove_analytics"),
            },
        ),
        (
            _("Analytics: Piwik"),
            {
                "fields": ("piwik_url", "piwik_site_id", "enable_piwik_site_analytics"),
            },
        ),
        (
            _("Analytics: Piwik PRO"),
            {
                "fields": (
                    "piwik_pro_url",
                    "piwik_pro_site_id",
                    "enable_piwik_pro_site_analytics",
                    "enable_piwik_pro_tag_manager",
                ),
            },
        ),
        (
            _("Analytics: GovMetric"),
            {
                "fields": (
                    "govmetric_source_id",
                    "govmetric_secure_guid",
                    "enable_govmetric_analytics",
                )
            },
        ),
    )
