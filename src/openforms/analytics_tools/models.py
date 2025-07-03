from collections.abc import Callable
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import AnalyticsTools
from .utils import CookieDict, get_domain_hash, update_analytics_tool
from .validators import validate_no_trailing_slash


@dataclass
class StringReplacement:
    needle: str
    field_name: str = ""
    callback: Callable[[CookieDict], str] = lambda cookie: cookie[
        "name"
    ]  # pragma: no cover


@dataclass
class ToolConfiguration:
    enable_field_name: str
    is_enabled_property: str
    replacements: list[StringReplacement] = field(default_factory=list)

    def has_enabled_toggled(
        self,
        original_config: "AnalyticsToolsConfiguration",
        current_config: "AnalyticsToolsConfiguration",
    ) -> bool:
        was_enabled = getattr(original_config, self.enable_field_name)
        is_now_enabled = getattr(current_config, self.enable_field_name)
        # XOR to detect toggle
        return was_enabled != is_now_enabled


DYNAMIC_TOOL_CONFIGURATION = {
    AnalyticsTools.google_analytics: ToolConfiguration(
        enable_field_name="enable_google_analytics",
        is_enabled_property="is_google_analytics_enabled",
    ),
    AnalyticsTools.matomo: ToolConfiguration(
        enable_field_name="enable_matomo_site_analytics",
        is_enabled_property="is_matomo_enabled",
        replacements=[
            StringReplacement(needle="SITE_ID", field_name="matomo_site_id"),
            StringReplacement(needle="SITE_URL", field_name="matomo_url"),
            StringReplacement(needle="DOMAIN_HASH", callback=get_domain_hash),
        ],
    ),
    AnalyticsTools.piwik_pro: ToolConfiguration(
        enable_field_name="enable_piwik_pro_site_analytics",
        is_enabled_property="is_piwik_pro_enabled",
        replacements=[
            StringReplacement(needle="SITE_ID", field_name="piwik_pro_site_id"),
            StringReplacement(needle="SITE_URL", field_name="piwik_pro_url"),
            StringReplacement(needle="DOMAIN_HASH", callback=get_domain_hash),
        ],
    ),
    AnalyticsTools.piwik_pro_tag_manager: ToolConfiguration(
        enable_field_name="enable_piwik_pro_tag_manager",
        is_enabled_property="is_piwik_pro_tag_manager_enabled",
        replacements=[
            StringReplacement(needle="SITE_ID", field_name="piwik_pro_site_id"),
            StringReplacement(needle="SITE_URL", field_name="piwik_pro_url"),
            StringReplacement(needle="DOMAIN_HASH", callback=get_domain_hash),
        ],
    ),
    AnalyticsTools.piwik: ToolConfiguration(
        enable_field_name="enable_piwik_site_analytics",
        is_enabled_property="is_piwik_enabled",
        replacements=[
            StringReplacement(needle="SITE_ID", field_name="piwik_site_id"),
            StringReplacement(needle="SITE_URL", field_name="piwik_url"),
            StringReplacement(needle="DOMAIN_HASH", callback=get_domain_hash),
        ],
    ),
    AnalyticsTools.siteimprove: ToolConfiguration(
        enable_field_name="enable_siteimprove_analytics",
        is_enabled_property="is_siteimprove_enabled",
    ),
    AnalyticsTools.govmetric: ToolConfiguration(
        enable_field_name="enable_govmetric_analytics",
        is_enabled_property="is_govmetric_enabled",
        replacements=[
            StringReplacement(
                needle="SOURCE_ID_FORM_FINISHED",
                field_name="govmetric_source_id_form_finished",
            ),
            StringReplacement(needle="DOMAIN_HASH", callback=get_domain_hash),
        ],
    ),
    AnalyticsTools.expoints: ToolConfiguration(
        enable_field_name="enable_expoints_analytics",
        is_enabled_property="is_expoints_enabled",
    ),
}


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
        _("enable Piwik PRO Site Analytics"),
        default=False,
        help_text=_("Enabling this installs Piwik PRO Analytics"),
    )
    enable_piwik_pro_tag_manager = models.BooleanField(
        _("enable piwik Pro Tag Manager"),
        default=False,
        help_text=_("Enabling this installs Piwik PRO Tag Manager."),
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
    govmetric_source_id_form_aborted = models.CharField(
        _("GovMetric source ID form aborted"),
        max_length=10,
        blank=True,
        help_text=_(
            "Your GovMetric source ID for when a form is aborted - This is created by KLANTINFOCUS when a list of "
            "questions is created. It is a numerical value that is unique per set of questions."
        ),
    )
    govmetric_secure_guid_form_aborted = models.CharField(
        _("GovMetric secure GUID form aborted"),
        blank=True,
        max_length=50,
        help_text=_(
            "Your GovMetric secure GUID for when a form is aborted - This is an optional value. "
            "It is created by KLANTINFOCUS when a list  of questions is created. "
            "It is a string that is unique per set of questions."
        ),
    )
    govmetric_source_id_form_finished = models.CharField(
        _("GovMetric source ID form finished"),
        max_length=10,
        blank=True,
        help_text=_(
            "Your GovMetric source ID for when a form is finished - This is created by KLANTINFOCUS when a list of "
            "questions is created. It is a numerical value that is unique per set of questions."
        ),
    )
    govmetric_secure_guid_form_finished = models.CharField(
        _("GovMetric secure GUID form finished"),
        blank=True,
        max_length=50,
        help_text=_(
            "Your GovMetric secure GUID for when a form is finished - This is an optional value. "
            "It is created by KLANTINFOCUS when a list  of questions is created. "
            "It is a string that is unique per set of questions."
        ),
    )
    enable_govmetric_analytics = models.BooleanField(
        _("enable GovMetric analytics"),
        default=False,
        help_text=_(
            "This enables GovMetric to collect data while a user fills in a form and it adds a button at the "
            "end of a form to fill in a client satisfaction survey."
        ),
    )

    expoints_organization_name = models.SlugField(
        _("Expoints organization name"),
        blank=True,
        max_length=50,
        help_text=_(
            "The name of your organization as registered in Expoints. This is used to construct the URL "
            "to communicate with Expoints."
        ),
    )
    expoints_config_uuid = models.CharField(
        _("Expoints configuration identifier"),
        blank=True,
        max_length=50,
        help_text=_(
            "The UUID used to retrieve the configuration from Expoints to initialize the client satisfaction survey."
        ),
    )
    expoints_use_test_mode = models.BooleanField(
        _("use Expoints test mode"),
        default=False,
        help_text=_(
            "Indicates whether or not the test mode should be enabled. If enabled, filled out surveys won't actually "
            "be sent, to avoid cluttering Expoints while testing."
        ),
    )
    enable_expoints_analytics = models.BooleanField(
        _("enable Expoints analytics"),
        default=False,
        help_text=_(
            "This adds a button at the end of a form to fill in a client satisfaction survey using Expoints."
        ),
    )

    analytics_cookie_consent_group = models.ForeignKey(
        "cookie_consent.CookieGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
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
    def is_piwik_pro_tag_manager_enabled(self) -> bool:
        return (
            self.piwik_pro_url
            and self.piwik_pro_site_id
            and self.enable_piwik_pro_tag_manager
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

    @property
    def is_govmetric_enabled(self) -> bool:
        return (
            self.govmetric_source_id_form_finished
            and self.govmetric_source_id_form_aborted
            and self.enable_govmetric_analytics
        )

    @property
    def is_expoints_enabled(self) -> bool:
        return (
            self.expoints_organization_name
            and self.expoints_config_uuid
            and self.enable_expoints_analytics
        )

    def save(self, *args, **kwargs):
        # If instance is being created, we can't find original values
        # (we use the _state API and not self.pk because `SingletonModel` hardcodes the PK).
        if self._state.adding:
            return super().save(*args, **kwargs)

        original_object = self.__class__.objects.get(pk=self.pk)

        # For each analytics provider, check if the configuration was changed and thus
        # the dynamic CSP/cookie configuration needs to be updated.
        for tool, tool_configuration in DYNAMIC_TOOL_CONFIGURATION.items():
            enabled_toggled = tool_configuration.has_enabled_toggled(
                original_object, self
            )
            # if the config was not changed, there's nothing to do
            if not enabled_toggled:
                continue

            is_currently_enabled = getattr(self, tool_configuration.is_enabled_property)
            update_analytics_tool(self, tool, is_currently_enabled, tool_configuration)

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
        if (
            self.enable_piwik_pro_tag_manager
            and not self.is_piwik_pro_tag_manager_enabled
        ):
            raise ValidationError(
                _(
                    "If you enable {analytics_tool}, you must fill out all the required fields"
                ).format(analytics_tool="Tag Manager")
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
        if self.enable_piwik_pro_site_analytics and self.enable_piwik_pro_tag_manager:
            raise ValidationError(
                _("Piwik Pro Analytics and Tag Manager can't be both activated"),
                code="invalid_together",
            )
        if self.enable_govmetric_analytics and not self.is_govmetric_enabled:
            raise ValidationError(
                _(
                    "If you enable GovMetric, you need to provide the source ID for all languages (the same one can be reused)."
                )
            )
        if self.enable_expoints_analytics and not self.is_expoints_enabled:
            raise ValidationError(
                _(
                    "If you enable Expoints, you need to provide the source ID for all languages (the same one can be reused)."
                )
            )
        super().clean()
