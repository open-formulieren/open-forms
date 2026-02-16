from functools import partial

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.functional import lazystr
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from glom import glom
from solo.models import SingletonModel
from tinymce.models import HTMLField
from zgw_consumers.models import Service

from openforms.data_removal.constants import RemovalMethods
from openforms.emails.validators import URLSanitationValidator
from openforms.template import (
    extract_variables_used,
    openforms_backend,
    render_from_string,
)
from openforms.template.validators import DjangoTemplateValidator
from openforms.translations.utils import ensure_default_language
from openforms.utils.fields import SVGOrImageField
from openforms.utils.translations import runtime_gettext
from openforms.utils.validators import IdTemplateValidator

from ..constants import FamilyMembersDataAPIChoices, UploadFileType
from ..utils import verify_clamav_connection
from .theme import Theme


@ensure_default_language()
def _render(filename: str, *args, **kwargs):
    return lazystr(render_to_string(filename, *args, **kwargs).strip())


get_confirmation_email_subject = partial(_render, "emails/confirmation/subject.txt")
get_confirmation_email_content = partial(_render, "emails/confirmation/content.html")


class GlobalConfigurationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("default_theme")


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

    # Confirmation page content
    submission_confirmation_title = models.CharField(
        _("submission confirmation title"),
        max_length=200,
        help_text=_(
            "The content of the confirmation page title. You can (and should) include "
            "the 'public_reference' variable (using expression '{{ public_reference }}') "
            "so the users have a reference in case they need to contact the customer "
            "service."
        ),
        default=runtime_gettext(_("Confirmation: {{ public_reference }}")),
        validators=[DjangoTemplateValidator()],
    )
    submission_confirmation_template = HTMLField(
        _("submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data."
        ),
        default=runtime_gettext(_("Thank you for submitting this form.")),
        validators=[DjangoTemplateValidator()],
    )
    submission_report_download_link_title = models.CharField(
        verbose_name=_("submission report download link title"),
        max_length=128,
        help_text=_("The title of the link to download the report of a submission."),
        default=runtime_gettext(_("Download PDF")),
    )
    cosign_submission_confirmation_title = models.CharField(
        _("cosign submission confirmation title"),
        max_length=200,
        help_text=_(
            "The content of the confirmation page title for submissions requiring "
            "cosigning."
        ),
        default=runtime_gettext(_("Request not complete yet")),
        validators=[DjangoTemplateValidator()],
    )
    cosign_submission_confirmation_template = HTMLField(
        _("cosign submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page for submissions requiring "
            "cosigning. The variables 'public_reference' and 'cosigner_email' are "
            "available (using expressions '{{ public_reference }}' and "
            "'{{ cosigner_email }}', respectively). We strongly advise you to include "
            "the 'public_reference' in case users need to contact the customer "
            "service."
        ),
        default=partial(_render, "config/default_cosign_submission_confirmation.html"),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            )
        ],
    )

    # Email templates
    confirmation_email_subject = models.CharField(
        _("subject"),
        max_length=1000,
        help_text=_(
            "Subject of the confirmation email message. Can be overridden on the form level"
        ),
        default=get_confirmation_email_subject,
        validators=[DjangoTemplateValidator()],
    )
    confirmation_email_content = HTMLField(
        _("content"),
        help_text=_(
            "Content of the confirmation email message. Can be overridden on the form level"
        ),
        default=get_confirmation_email_content,
        validators=[
            DjangoTemplateValidator(
                required_template_tags=[
                    "appointment_information",
                    "payment_information",
                ],
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )
    save_form_email_subject = models.CharField(
        _("subject"),
        max_length=1000,
        help_text=_("Subject of the save form email message."),
        default=partial(_render, "emails/save_form/subject.txt"),
        validators=[DjangoTemplateValidator()],
    )
    save_form_email_content = HTMLField(
        _("content"),
        help_text=_("Content of the save form email message."),
        default=partial(_render, "emails/save_form/content.html"),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend"),
            URLSanitationValidator(),
        ],
    )

    cosign_request_template = HTMLField(
        _("co-sign request template"),
        help_text=_(
            "Content of the co-sign request email. The available template "
            "variables are: 'form_name', 'submission_date', 'form_url' and 'code'."
        ),
        default=partial(_render, "emails/co_sign/request.html"),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend"),
            URLSanitationValidator(),
        ],
    )
    cosign_confirmation_email_subject = models.CharField(
        _("cosign subject"),
        max_length=1000,
        help_text=_(
            "Subject of the confirmation email message when the form requires "
            "cosigning. Can be overridden on the form level."
        ),
        default=partial(_render, "emails/confirmation/cosign_subject.txt"),
        validators=[DjangoTemplateValidator()],
    )
    cosign_confirmation_email_content = HTMLField(
        _("cosign content"),
        help_text=_(
            "Content of the confirmation email message when the form requires "
            "cosigning. Can be overridden on the form level."
        ),
        default=partial(_render, "emails/confirmation/cosign_content.html"),
        validators=[
            DjangoTemplateValidator(
                required_template_tags=[
                    "payment_information",
                    "cosign_information",
                ],
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )

    email_verification_request_subject = models.CharField(
        _("subject"),
        max_length=1000,
        help_text=_("Subject of the email verification email."),
        default=partial(_render, "emails/email_verification/subject.txt"),
        validators=[DjangoTemplateValidator()],
    )
    email_verification_request_content = HTMLField(
        _("content"),
        help_text=_("Content of the email verification email message."),
        default=partial(_render, "emails/email_verification/request.html"),
        validators=[
            DjangoTemplateValidator(),
            URLSanitationValidator(),
        ],
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
        _("back to form text"),
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
        _("previous step text"),
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
    form_fields_required_default = models.BooleanField(
        verbose_name=_("Mark form fields 'required' by default"),
        default=False,
        help_text=_(
            "Whether the checkbox 'required' on form fields should be checked by default."
        ),
    )
    form_display_required_with_asterisk = models.BooleanField(
        verbose_name=_("Mark required fields with asterisks"),
        default=True,
        help_text=_(
            "If checked, required fields are marked with an asterisk and optional "
            "fields are unmarked. If unchecked, optional fields will be marked with "
            "'(optional)' and required fields are unmarked."
        ),
    )
    form_upload_default_file_types = ArrayField(
        models.CharField(max_length=256, choices=UploadFileType.choices),
        verbose_name=_("Default allowed file upload types"),
        help_text=_(
            "Provide a list of default allowed file upload types. If empty, all extensions are allowed."
        ),
        default=list,
        blank=True,
    )
    hide_non_applicable_steps = models.BooleanField(
        verbose_name=_("Hide non-applicable form steps"),
        default=False,
        help_text=_(
            "If checked, form steps that become non-applicable as a result of user "
            "input are hidden from the progress indicator display (by default, they "
            "are displayed but marked as non-applicable.)"
        ),
    )
    form_map_default_zoom_level = models.IntegerField(
        verbose_name=_("The default zoom level for the leaflet map."),
        validators=[MinValueValidator(0), MaxValueValidator(13)],
        default=13,
    )
    form_map_default_latitude = models.FloatField(
        verbose_name=_("The default latitude for the leaflet map."),
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0),
        ],
        default=52.1326332,
    )
    form_map_default_longitude = models.FloatField(
        verbose_name=_("The default longitude for the leaflet map."),
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0),
        ],
        default=5.291266,
    )
    # 'subdomain' styling & content configuration
    default_theme = models.OneToOneField(
        Theme,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("default theme"),
        help_text=_(
            "If no explicit theme is configured, the configured default theme "
            "will be used as a fallback."
        ),
    )

    favicon = SVGOrImageField(
        _("favicon"),
        upload_to="logo/",
        blank=True,
        help_text=_(
            "Allow the uploading of a favicon, .png .jpg .svg and .ico are compatible."
        ),
    )
    main_website = models.URLField(
        _("main website link"),
        blank=True,
        help_text=_(
            "URL to the main website. Used for the 'back to municipality website' link."
        ),
    )
    organization_name = models.CharField(
        _("organization name"),
        max_length=100,
        blank=True,
        help_text=_(
            "The name of your organization that will be used as label for elements "
            "like the logo."
        ),
    )

    # See https://gitdocumentatie.logius.nl/publicatie/dk/oin/#samenstelling-oin
    organization_oin = models.CharField(
        _("organization OIN"),
        max_length=20,
        blank=True,
        help_text=_("The OIN of the organization."),
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
        default=15,
        validators=[
            MinValueValidator(5),
            MaxValueValidator(
                15,
                message=_(
                    "Due to DigiD requirements this value has to be less than or equal to %(limit_value)s minutes."
                ),
            ),
        ],
        help_text=_(
            "Amount of time in minutes a user filling in a form can be inactive for before being logged out"
        ),
    )

    # global payment settings
    payment_order_id_template = models.CharField(
        _("Payment Order ID template"),
        # A somewhat arbitrary value, should be around 40 characters after template substitutions:
        max_length=48,
        default="{year}/{public_reference}/{uid}",
        help_text=_(
            "Template to use when generating payment order IDs. It should be alpha-numerical and can contain the '/._-' characters. "
            "You can use the placeholder tokens: {year}, {public_reference}, {uid}.",
        ),
        validators=[IdTemplateValidator()],
    )

    # Privacy policy related fields
    ask_privacy_consent = models.BooleanField(
        _("ask privacy consent"),
        default=True,
        help_text=_(
            "If enabled, the user will have to agree to the privacy policy before submitting a form."
        ),
    )
    privacy_policy_url = models.URLField(
        _("privacy policy URL"), blank=True, help_text=_("URL to the privacy policy")
    )
    privacy_policy_label = HTMLField(
        _("privacy policy label"),
        blank=True,
        help_text=_(
            "The label of the checkbox that prompts the user to agree to the privacy policy."
        ),
        default=runtime_gettext(
            _(
                "Yes, I have read the {% privacy_policy %} and explicitly agree to the "
                "processing of my submitted information."
            )
        ),
        validators=[
            DjangoTemplateValidator(
                required_template_tags=[
                    "privacy_policy",
                ],
                backend="openforms.template.openforms_backend",
            ),
        ],
    )

    # Statement of truth related fields
    ask_statement_of_truth = models.BooleanField(
        _("ask statement of truth"),
        default=False,
        help_text=_(
            "If enabled, the user will have to agree that they filled out the form "
            "truthfully before submitting it."
        ),
    )
    statement_of_truth_label = HTMLField(
        _("statement of truth label"),
        blank=True,
        help_text=_(
            "The label of the checkbox that prompts the user to agree that they filled "
            "out the form truthfully. Note that this field does not have templating "
            "support."
        ),
        default=runtime_gettext(
            _(
                "I declare that I have filled out the form truthfully and have not omitted "
                "any information."
            )
        ),
    )

    # Removing data configurations
    successful_submissions_removal_limit = models.PositiveIntegerField(
        _("successful submission removal limit"),
        default=7,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days successful submissions will remain before being removed"
        ),
    )
    successful_submissions_removal_method = models.CharField(
        _("successful submissions removal method"),
        max_length=50,
        choices=RemovalMethods.choices,
        default=RemovalMethods.delete_permanently,
        help_text=_("How successful submissions will be removed after the limit"),
    )
    incomplete_submissions_removal_limit = models.PositiveIntegerField(
        _("incomplete submission removal limit"),
        default=7,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days incomplete submissions will remain before being removed"
        ),
    )
    incomplete_submissions_removal_method = models.CharField(
        _("incomplete submissions removal method"),
        max_length=50,
        choices=RemovalMethods.choices,
        default=RemovalMethods.delete_permanently,
        help_text=_("How incomplete submissions will be removed after the limit"),
    )
    errored_submissions_removal_limit = models.PositiveIntegerField(
        _("errored submission removal limit"),
        default=30,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days errored submissions will remain before being removed"
        ),
    )
    errored_submissions_removal_method = models.CharField(
        _("errored submissions removal method"),
        max_length=50,
        choices=RemovalMethods.choices,
        default=RemovalMethods.delete_permanently,
        help_text=_("How errored submissions will be removed after the"),
    )
    all_submissions_removal_limit = models.PositiveIntegerField(
        _("all submissions removal limit"),
        default=90,
        validators=[MinValueValidator(0)],
        help_text=_("Amount of days when all submissions will be permanently deleted"),
    )

    registration_attempt_limit = models.PositiveIntegerField(
        _("default registration backend attempt limit"),
        default=5,
        validators=[MinValueValidator(1)],
        help_text=_(
            "How often we attempt to register the submission at the registration backend before giving up"
        ),
    )

    plugin_configuration = models.JSONField(
        _("plugin configuration"),
        blank=True,
        default=dict,
        help_text=_(
            "Configuration of plugins for authentication, payments, prefill, "
            "registrations and validation"
        ),
    )

    reference_lists_services = models.ManyToManyField(
        Service,
        verbose_name=_("reference lists services"),
        help_text=_(
            "List of services that are instances of the Referentielijsten API. "
            "The selected services will be shown as options when configuring "
            "select or selectboxes components to be populated from Referentielijsten."
        ),
        blank=True,
    )
    family_members_data_api = models.CharField(
        _("family members data api"),
        help_text=_("Which API to use to retrieve the data of the family members."),
        choices=FamilyMembersDataAPIChoices.choices,
        max_length=100,
        blank=True,
    )
    communication_preferences_portal_url = models.URLField(
        _("communication preferences portal url"),
        blank=True,
        help_text=_(
            "Url to the online portal where users can update their communication preferences. "
            "This is used by the profile component."
        ),
    )

    # search engine configuration
    allow_indexing_form_detail = models.BooleanField(
        _("Allow form page indexing"),
        default=True,
        help_text=_(
            "Whether form detail pages may be indexed and displayed in search engine "
            "result lists. Disable this to prevent listing."
        ),
    )

    enable_virus_scan = models.BooleanField(
        _("Enable virus scan"),
        default=False,
        help_text=_(
            "Whether the files uploaded by the users should be scanned by ClamAV virus scanner."
            "In case a file is found to be infected, the file is deleted."
        ),
    )
    clamav_host = models.CharField(
        _("ClamAV server hostname"),
        max_length=1000,
        help_text=_("Hostname or IP address where ClamAV is running."),
        blank=True,
    )

    clamav_port = models.PositiveIntegerField(
        _("ClamAV port number"),
        help_text=_("The TCP port on which ClamAV is listening."),
        null=True,
        blank=True,
        validators=[MaxValueValidator(65535)],
        default=3310,
    )

    clamav_timeout = models.PositiveSmallIntegerField(
        _("ClamAV socket timeout"),
        help_text=_("ClamAV socket timeout expressed in seconds (optional)."),
        null=True,
        blank=True,
        validators=[MaxValueValidator(60)],
    )

    recipients_email_digest = ArrayField(
        models.EmailField(),
        verbose_name=_("recipients email digest"),
        help_text=_(
            "The email addresses that should receive a daily report of items requiring attention."
        ),
        blank=True,
        default=list,
    )
    wait_for_payment_to_register = models.BooleanField(
        verbose_name=_("wait for payment to register"),
        help_text=_(
            "Should a submission be processed (sent to the registration backend) only after payment has been received?"
        ),
        default=False,
    )

    objects = GlobalConfigurationManager()

    class Meta:
        verbose_name = _("General configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    def render_privacy_policy_label(self) -> str:
        return render_from_string(
            self.privacy_policy_label,
            context={"global_configuration": self},
            backend=openforms_backend,
        )

    def plugin_enabled(self, module: str, plugin_identifier: str):
        enabled = glom(
            self.plugin_configuration,
            f"{module}.{plugin_identifier}.enabled",
            default=True,
        )
        assert isinstance(enabled, bool)
        return enabled

    def clean(self):
        if self.enable_virus_scan:
            if not self.clamav_host or self.clamav_port is None:
                raise ValidationError(
                    _(
                        "ClamAV host and port need to be configured if virus scan is enabled."
                    )
                )

            result = verify_clamav_connection(
                host=self.clamav_host,
                port=self.clamav_port,
                timeout=self.clamav_timeout,
            )
            if not result.can_connect:
                raise ValidationError(
                    _("Cannot connect to ClamAV: {error}").format(error=result.error)
                )

        return super().clean()

    def get_default_theme(self) -> Theme:
        """
        Use the configured default theme or create an in-memory instane on the fly
        if none is configured.
        """
        return self.default_theme or Theme()

    @property
    def cosign_request_template_has_link(self) -> bool:
        variables_used = extract_variables_used(
            self.cosign_request_template, backend=openforms_backend
        )
        return "form_url" in variables_used
