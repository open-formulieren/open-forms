from cookie_consent.models import CookieGroup

from openforms.analytics_tools.models import AnalyticsToolsConfiguration
from openforms.utils.tests.cache import clear_caches


class AnalyticsMixin:
    config: AnalyticsToolsConfiguration

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        (
            self.config.analytics_cookie_consent_group,
            _,
        ) = CookieGroup.objects.get_or_create(varname="analytical")

        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())
        self.addCleanup(clear_caches)
