from django.contrib.admin.options import get_content_type_for_model
from django.test import TestCase, override_settings

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None)
class CSPIdentifierTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.gtm_code = "GTM-XXXX"
        cls.ga_code = "UA-XXXXX-Y"
        cls.matomo_url = "https://example.com"

    def disabling_analytics_does_not_delete_unrelated_csp_settings(self):
        self.config.gtm_code = self.ga_code
        self.config.ga_code = self.gtm_code
        self.config.enable_google_analytics = True

        self.config.matomo_url = self.matomo_url
        self.config.matomo_site_id = "1234"
        self.config.enable_matomo_site_analytics = True
        self.config.clean()
        self.config.save()

        csp_settings = CSPSetting.objects.filter(
            content_type=get_content_type_for_model(self.config),
            object_id=str(self.config.pk),
        )

        assert csp_settings.count() == 2

        self.config.enable_google_analytics = False
        self.config.save()

        try:
            CSPSetting.objects.get(identifier=AnalyticsTools.matomo)
        except CSPSetting.DoesNotExist:
            self.fail("CSPSetting instance should exist")
