from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel
from tinymce.models import HTMLField


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

    class Meta:
        verbose_name = _("General configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)
