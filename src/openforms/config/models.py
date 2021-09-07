from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel
from tinymce.models import HTMLField

from openforms.data_removal.constants import RemovalMethods
from openforms.utils.fields import SVGOrImageField
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

    # 'subdomain' styling & content configuration
    # FIXME: do not expose this field via the API to non-admin users! There is not
    # sufficient input validation to protect against the SVG attack surface. The SVG
    # is rendered by the browser of end-users.
    #
    # See https://www.fortinet.com/blog/threat-research/scalable-vector-graphics-attack-surface-anatomy
    #
    # * XSS
    # * HTML Injection
    # * XML entity processing
    # * DoS
    logo = SVGOrImageField(
        _("municipality logo"),
        upload_to="logo/",
        blank=True,
        help_text=_(
            "Upload the municipality logo, visible to users filling out forms. We "
            "advise dimensions around 150px by 75px. SVG's are allowed."
        ),
    )
    main_website = models.URLField(
        _("main website link"),
        blank=True,
        help_text=_(
            "URL to the main website. Used for the 'back to municipality website' link."
        ),
    )
    # the configuration of the values of available design tokens, following the
    # format outlined in https://github.com/amzn/style-dictionary#design-tokens which
    # is used by NLDS.
    # TODO: specify a serializer describing the supported design parameters to use for
    # validation.
    # Example:
    # {
    #   "of": {
    #     "button": {
    #       "background-color": {
    #         "value": "fuchsia"
    #       }
    #     }
    #   }
    # }
    #
    # TODO: later on, we should have the ability to include a dist/index.css file containing
    # the municipality styles. This would then allow us to use references to existing design
    # tokens or even have the OF-specific design tokens included in the municipality dist
    # already, see for example https://unpkg.com/@utrecht/design-tokens@1.0.0-alpha.20/dist/index.css

    design_token_values = JSONField(
        _("design token values"),
        blank=True,
        default=dict,
        help_text=_(
            "Values of various style parameters, such as border radii, background "
            "colors... Note that this is advanced usage. Any available but un-specified "
            "values will use fallback default values."
        ),
    )

    # session timeouts

    admin_session_timeout = models.PositiveIntegerField(
        _("admin session timeout"),
        default=60,
        validators=[MinValueValidator(5)],
        help_text=_(
            "Amount of time in minutes the admin can be inactive for before being logged out"
        ),
    )
    form_session_timeout = models.PositiveIntegerField(
        _("form session timeout"),
        default=60,
        validators=[MinValueValidator(5)],
        help_text=_(
            "Amount of time in minutes a user filling in a form can be inactive for before being logged out"
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

    # debug/feature flags
    enable_react_form = models.BooleanField(
        _("enable React form page"),
        default=True,
        help_text=_(
            "If enabled, the admin page to create forms will use the new React page."
        ),
    )
    enable_demo_plugins = models.BooleanField(
        _("enable demo plugins"),
        default=False,
        help_text=_("If enabled, the admin allows selection of demo backend plugins."),
    )

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

    # Removing data configurations
    successful_submissions_removal_limit = models.PositiveIntegerField(
        _("successful submission removal limit"),
        default=7,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days successful submissions will remain before being removed"
        ),
    )
    successful_submissions_removal_method = models.CharField(
        _("successful submissions removal method"),
        max_length=50,
        choices=RemovalMethods,
        default=RemovalMethods.delete_permanently,
        help_text=_("How successful submissions will be removed after the limit"),
    )
    incomplete_submissions_removal_limit = models.PositiveIntegerField(
        _("incomplete submission removal limit"),
        default=7,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days incomplete submissions will remain before being removed"
        ),
    )
    incomplete_submissions_removal_method = models.CharField(
        _("incomplete submissions removal method"),
        max_length=50,
        choices=RemovalMethods,
        default=RemovalMethods.delete_permanently,
        help_text=_("How incomplete submissions will be removed after the limit"),
    )
    errored_submissions_removal_limit = models.PositiveIntegerField(
        _("errored submission removal limit"),
        default=30,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days errored submissions will remain before being removed"
        ),
    )
    errored_submissions_removal_method = models.CharField(
        _("errored submissions removal method"),
        max_length=50,
        choices=RemovalMethods,
        default=RemovalMethods.delete_permanently,
        help_text=_("How errored submissions will be removed after the"),
    )
    all_submissions_removal_limit = models.PositiveIntegerField(
        _("all submissions removal limit"),
        default=90,
        validators=[MinValueValidator(1)],
        help_text=_("Amount of days when all submissions will be permanently deleted"),
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
