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
        _("form previous text"),
        max_length=50,
        default=runtime_gettext(_("Previous page")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "go to the previous step"
        ),
    )
    form_change_text = models.CharField(
        _("form change text"),
        max_length=50,
        default=runtime_gettext(_("Change")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "change a certain step"
        ),
    )
    form_confirm_text = models.CharField(
        _("form confirm text"),
        max_length=50,
        default=runtime_gettext(_("Confirm")),
        help_text=_(
            "The text that will be displayed in the overview page to "
            "confirm the form is filled in correctly"
        ),
    )
    form_begin_text = models.CharField(
        _("form begin text"),
        max_length=50,
        default=runtime_gettext(_("Begin form")),
        help_text=_(
            "The text that will be displayed at the start of the form to "
            "indicate the user can begin to fill in the form"
        ),
    )

    form_step_previous_text = models.CharField(
        _("form step previous text"),
        max_length=50,
        default=runtime_gettext(_("Previous page")),
        help_text=_(
            "The text that will be displayed in the form step to go to the previous step"
        ),
    )
    form_step_save_text = models.CharField(
        _("form step save text"),
        max_length=50,
        default=runtime_gettext(_("Save current information")),
        help_text=_(
            "The text that will be displayed in the form step to save the current information"
        ),
    )
    form_step_next_text = models.CharField(
        _("form step next text"),
        max_length=50,
        default=runtime_gettext(_("Next")),
        help_text=_(
            "The text that will be displayed in the form step to go to the next step"
        ),
    )

    class Meta:
        verbose_name = _("General configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)
