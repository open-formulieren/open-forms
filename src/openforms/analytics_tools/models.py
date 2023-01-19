from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import AnalyticsTools
from .utils import (
    get_cookies,
    get_csp,
    get_domain_hash,
    update_analytical_cookies,
    update_csp,
)
from .validators import validate_no_trailing_slash


class AnalyticsToolsConfiguration(SingletonModel):

    gtm_code = models.CharField(
        _("Google Tag Manager code"),
        max_length=50,
        blank=True,
        help_text=_(
            "Typically looks like 'GTM-XXXX'. Supplying this installs Google Tag Manager."
        ),
    )
    ga_code = models.CharField(
        _("Google Analytics code"),
        max_length=50,
        blank=True,
        help_text=_(
            "Typically looks like 'UA-XXXXX-Y'. Supplying this installs Google Analytics."
        ),
    )
    enable_google_analytics = models.BooleanField(
        _("enable google analytics"),
        default=False,
        help_text=_("Enabling this installs Google Analytics"),
    )
    matomo_url = models.URLField(
        _("Matomo server URL"),
        max_length=255,
        blank=True,
        validators=[validate_no_trailing_slash],
        help_text=_(
            "The base URL of your Matomo server, e.g. 'https://matomo.example.com'."
        ),
    )
    matomo_site_id = models.PositiveIntegerField(
        _("Matomo site ID"),
        blank=True,
        null=True,
        help_text=_("The 'idsite' of the website you're tracking in Matomo."),
    )
    enable_matomo_site_analytics = models.BooleanField(
        _("enable matomo site analytics"),
        default=False,
        help_text=_("Enabling this installs Matomo"),
    )
    piwik_url = models.URLField(
        _("Piwik server URL"),
        max_length=255,
        blank=True,
        validators=[validate_no_trailing_slash],
        help_text=_(
            "The base URL of your Piwik server, e.g. 'https://piwik.example.com'."
        ),
    )
    piwik_site_id = models.PositiveIntegerField(
        _("Piwik site ID"),
        blank=True,
        null=True,
        help_text=_("The 'idsite' of the website you're tracking in Piwik."),
    )
    enable_piwik_site_analytics = models.BooleanField(
        _("enable piwik site analytics"),
        default=False,
        help_text=_("Enabling this installs Piwik"),
    )
    piwik_pro_url = models.URLField(
        _("Piwik PRO server URL"),
        max_length=255,
        blank=True,
        validators=[validate_no_trailing_slash],
        help_text=_(
            "The base URL of your Piwik PRO server, e.g. 'https://your-instance-name.piwik.pro'."
        ),
    )
    piwik_pro_site_id = models.UUIDField(
        _("Piwik PRO site ID"),
        blank=True,
        null=True,
        help_text=_(
            "The 'idsite' of the website you're tracking in Piwik PRO. https://help.piwik.pro/support/questions/find-website-id/"
        ),
    )

    enable_piwik_pro_site_analytics = models.BooleanField(
        _("enable piwik pro site analytics"),
        default=False,
        help_text=_("Enabling this installs Piwik Pro"),
    )
    siteimprove_id = models.CharField(
        _("SiteImprove ID"),
        max_length=10,
        blank=True,
        help_text=_(
            "Your SiteImprove ID - you can find this from the embed snippet example, "
            "which should contain a URL like '//siteimproveanalytics.com/js/siteanalyze_XXXXX.js'. "
            "The XXXXX is your ID."
        ),
    )

    enable_siteimprove_analytics = models.BooleanField(
        _("enable siteImprove analytics"),
        default=False,
        help_text=_("Enabling this installs SiteImprove"),
    )

    analytics_cookie_consent_group = models.ForeignKey(
        "cookie_consent.CookieGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_(
            "The cookie group used for analytical cookies. The analytics scripts are "
            "loaded only if this cookie group is accepted by the end-user."
        ),
    )

    class Meta:
        verbose_name = _("Analytics tools configuration")

    @property
    def is_matomo_enabled(self) -> bool:
        return (
            self.matomo_url
            and self.matomo_site_id
            and self.enable_matomo_site_analytics
            and self.analytics_cookie_consent_group
        )

    @property
    def is_piwik_enabled(self) -> bool:
        return (
            self.piwik_url
            and self.piwik_site_id
            and self.enable_piwik_site_analytics
            and self.analytics_cookie_consent_group
        )

    @property
    def is_piwik_pro_enabled(self) -> bool:
        return (
            self.piwik_pro_url
            and self.piwik_pro_site_id
            and self.enable_piwik_pro_site_analytics
            and self.analytics_cookie_consent_group
        )

    @property
    def is_siteimprove_enabled(self) -> bool:
        return (
            self.siteimprove_id
            and self.enable_siteimprove_analytics
            and self.analytics_cookie_consent_group
        )

    @property
    def is_google_analytics_enabled(self) -> bool:
        return (
            self.ga_code
            and self.gtm_code
            and self.enable_google_analytics
            and self.analytics_cookie_consent_group
        )

    def save(self, *args, **kwargs):
        # If instance is being created, we can't find original values
        if self._state.adding:
            return super().save(*args, **kwargs)
        original_object = self.__class__.objects.get(pk=self.pk)
        # For each analytics provider, we check if :
        # - the value of the provider's boolean field is changing
        if original_object.enable_google_analytics != self.enable_google_analytics:
            self.update_analytics_tool(
                AnalyticsTools.google_analytics, self.is_google_analytics_enabled, []
            )
        if (
            original_object.enable_matomo_site_analytics
            != self.enable_matomo_site_analytics
        ):
            string_replacements_list = [
                ("SITE_ID", self.matomo_site_id),
                ("SITE_URL", self.matomo_url),
                (
                    "DOMAIN_HASH",
                    lambda cookie: get_domain_hash(
                        settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                    ),
                ),
            ]
            self.update_analytics_tool(
                AnalyticsTools.matomo, self.is_matomo_enabled, string_replacements_list
            )
        if (
            original_object.enable_piwik_pro_site_analytics
            != self.enable_piwik_pro_site_analytics
        ):

            string_replacements_list = [
                ("SITE_ID", self.piwik_pro_site_id),
                ("SITE_URL", self.piwik_pro_url),
                (
                    "DOMAIN_HASH",
                    lambda cookie: get_domain_hash(
                        settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                    ),
                ),
            ]
            self.update_analytics_tool(
                AnalyticsTools.piwik_pro,
                self.is_piwik_pro_enabled,
                string_replacements_list,
            )
        if (
            original_object.enable_piwik_site_analytics
            != self.enable_piwik_site_analytics
        ):

            string_replacements_list = [
                ("SITE_ID", self.piwik_site_id),
                ("SITE_URL", self.piwik_url),
                (
                    "DOMAIN_HASH",
                    lambda cookie: get_domain_hash(
                        settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                    ),
                ),
            ]

            self.update_analytics_tool(
                AnalyticsTools.piwik, self.is_piwik_enabled, string_replacements_list
            )
        if (
            original_object.enable_siteimprove_analytics
            != self.enable_siteimprove_analytics
        ):
            self.update_analytics_tool(
                AnalyticsTools.siteimprove, self.is_siteimprove_enabled, []
            )
        super().save(*args, **kwargs)

    def clean(self):
        if self.enable_google_analytics and not self.is_google_analytics_enabled:
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="Google Analytics")
            )
        if self.enable_matomo_site_analytics and not self.is_matomo_enabled:
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="Matomo")
            )
        if self.enable_piwik_pro_site_analytics and not self.is_piwik_pro_enabled:
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="Piwik Pro")
            )
        if self.enable_piwik_site_analytics and not self.is_piwik_enabled:
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="Piwik")
            )
        if self.enable_siteimprove_analytics and not self.is_siteimprove_enabled:
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="SiteImprove")
            )
        super().clean()

    def update_analytics_tool(
        self,
        analytics_tool: str,
        is_activated: bool,
        string_replacements_list: List[tuple],
    ):
        from openforms.logging import logevent

        if is_activated:
            logevent.enabling_analytics_tool(self, analytics_tool)
        else:
            logevent.disabling_analytics_tool(self, analytics_tool)

        csps = get_csp(analytics_tool, string_replacements_list)
        cookies = get_cookies(analytics_tool, string_replacements_list)
        update_analytical_cookies(
            cookies,
            create=is_activated,
            cookie_consent_group_id=self.analytics_cookie_consent_group.id,
        )
        update_csp(csps, create=is_activated)
