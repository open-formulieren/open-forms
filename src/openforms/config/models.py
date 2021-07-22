from django.core.validators import MinValueValidator
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel
from tinymce.models import HTMLField

from openforms.utils.translations import runtime_gettext


class GlobalConfiguration(SingletonModel):
    email_template_netloc_allowlist = ArrayField(
        models.CharField(max_length=1000),
        verbose_name=_("allowed email domain names"),
        help_text=_(
            "Provide a list of allowed domains (without 'https://www')."
            "Hyperlinks in a (confirmation) email are removed, unless the "
            "domain is provided here."
        ),
        blank=True,
        default=list,
    )
    enable_react_form = models.BooleanField(
        _("enable React form page"),
        default=False,
        help_text=_(
            "If enabled, the admin page to create forms will use the new React page."
        ),
    )

    # for testing purposes!
    default_test_bsn = models.CharField(
        _("default test BSN"),
        blank=True,
        default="",
        max_length=9,
        help_text=_(
            "When provided, submissions that are started will have this BSN set as "
            "default for the session. Useful to test/demo prefill functionality."
        ),
    )
    default_test_kvk = models.CharField(
        _("default test KvK Number"),
        blank=True,
        default="",
        max_length=9,
        help_text=_(
            "When provided, submissions that are started will have this KvK Number set as "
            "default for the session. Useful to test/demo prefill functionality."
        ),
    )

    display_sdk_information = models.BooleanField(
        _("display SDK information"),
        default=False,
        help_text=_("When enabled, information about the used SDK is displayed."),
    )
    submission_confirmation_template = HTMLField(
        _("submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data."
        ),
        default="Thank you for submitting this form.",
    )
    allow_empty_initiator = models.BooleanField(
        _("allow empty initiator"),
        default=False,
        help_text=_(
            "When enabled and the submitter is not authenticated, a case is "
            "created without any initiator. Otherwise, a fake initiator is "
            "added with BSN 111222333."
        ),
    )

    form_previous_text = models.CharField(
        _("previous text"),
        max_length=50,
        default=runtime_gettext(_("Previous page")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "go to the previous step"
        ),
    )
    form_change_text = models.CharField(
        _("change text"),
        max_length=50,
        default=runtime_gettext(_("Change")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "change a certain step"
        ),
    )
    form_confirm_text = models.CharField(
        _("confirm text"),
        max_length=50,
        default=runtime_gettext(_("Confirm")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "confirm the form is filled in correctly"
        ),
    )
    form_begin_text = models.CharField(
        _("begin text"),
        max_length=50,
        default=runtime_gettext(_("Begin form")),
        help_text=_(
            "The text that will be displayed at the start of the form to "
            "indicate the user can begin to fill in the form"
        ),
    )

    form_step_previous_text = models.CharField(
        _("step previous text"),
        max_length=50,
        default=runtime_gettext(_("Previous page")),
        help_text=_(
            "The text that will be displayed in the form step to go to the previous step"
        ),
    )
    form_step_save_text = models.CharField(
        _("step save text"),
        max_length=50,
        default=runtime_gettext(_("Save current information")),
        help_text=_(
            "The text that will be displayed in the form step to save the current information"
        ),
    )
    form_step_next_text = models.CharField(
        _("step next text"),
        max_length=50,
        default=runtime_gettext(_("Next")),
        help_text=_(
            "The text that will be displayed in the form step to go to the next step"
        ),
    )

    admin_session_timeout = models.PositiveIntegerField(
        _("admin session timeout"),
        default=3600,
        validators=[MinValueValidator(60)],
        help_text=_(
            "Amount of time in seconds the admin can be inactive for before being logged out"
        ),
    )
    form_session_timeout = models.PositiveIntegerField(
        _("form session timeout"),
        default=3600,
        help_text=_(
            "Amount of time in seconds a user filling in a form can be inactive for before being logged out"
        ),
    )

    # analytics/tracking
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
    matomo_url = models.CharField(
        _("Matomo server URL"),
        max_length=255,
        blank=True,
        help_text=_("The base URL of your Matomo server, e.g. 'matomo.example.com'."),
    )
    matomo_site_id = models.PositiveIntegerField(
        _("Matomo site ID"),
        blank=True,
        null=True,
        help_text=_("The 'idsite' of the website you're tracking in Matomo."),
    )
    piwik_url = models.CharField(
        _("Piwik server URL"),
        max_length=255,
        blank=True,
        help_text=_("The base URL of your Piwik server, e.g. 'piwik.example.com'."),
    )
    piwik_site_id = models.PositiveIntegerField(
        _("Piwik site ID"),
        blank=True,
        null=True,
        help_text=_("The 'idsite' of the website you're tracking in Piwik."),
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
        verbose_name = _("General configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    @property
    def matomo_enabled(self) -> bool:
        return self.matomo_url and self.matomo_site_id

    @property
    def piwik_enabled(self) -> bool:
        return self.piwik_url and self.piwik_site_id

    @property
    def siteimprove_enabled(self) -> bool:
        return bool(self.siteimprove_id)
