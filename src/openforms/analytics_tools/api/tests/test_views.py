from unittest.mock import patch

from django.test import override_settings

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ...models import AnalyticsToolsConfiguration


class TestAnalyticsToolsConfigViews(APITestCase):
    @patch("openforms.analytics_tools.api.views.AnalyticsToolsConfiguration.get_solo")
    def test_get_language_specific_govmetric_source_id(self, m_config):
        m_config.return_value = AnalyticsToolsConfiguration(
            enable_govmetric_analytics=True,
            govmetric_source_id_en="1234",
            govmetric_source_id_nl="4321",
        )

        with override_settings(LANGUAGE_CODE="en"):
            response_en = self.client.get(
                reverse("api:analytics_tools:analytics-tools-config-info")
            )

        with override_settings(LANGUAGE_CODE="nl"):
            response_nl = self.client.get(
                reverse("api:analytics_tools:analytics-tools-config-info")
            )

        data_en = response_en.json()
        data_nl = response_nl.json()

        self.assertEqual(data_en["govmetricSourceId"], "1234")
        self.assertEqual(data_nl["govmetricSourceId"], "4321")
