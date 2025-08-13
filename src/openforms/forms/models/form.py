import uuid as _uuid
from collections.abc import Iterator
from contextlib import suppress
from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.db.models.manager import BaseManager
from django.utils.formats import localize
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _, override

import structlog
from autoslug import AutoSlugField
from privates.fields import PrivateMediaFileField
from rest_framework.reverse import reverse
from tinymce.models import HTMLField

from csp_post_processor.fields import CSPPostProcessedWYSIWYGField
from openforms.authentication.registry import register as authentication_register
from openforms.config.models import GlobalConfiguration
from openforms.data_removal.constants import RemovalMethods
from openforms.formio.typing import Component
from openforms.formio.validators import variable_key_validator
from openforms.payments.fields import PaymentBackendChoiceField
from openforms.payments.registry import register as payment_register
from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.registrations.registry import register as registration_register
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin
from openforms.variables.constants import FormVariableSources

from ..constants import StatementCheckboxChoices, SubmissionAllowedChoices
from .utils import literal_getter

User = get_user_model()
logger = structlog.stdlib.get_logger(__name__)

if TYPE_CHECKING:
    from . import FormAuthenticationBackend


class FormQuerySet(models.QuerySet):
    def live(self):
        return self.filter(active=True, _is_deleted=False)


class FormManager(models.Manager.from_queryset(FormQuerySet)):
    if TYPE_CHECKING:

        def live(self) -> FormQuerySet: ...


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    name = models.CharField(_("name"), max_length=150)
    internal_name = models.CharField(
        _("internal name"),
        blank=True,
        max_length=150,
        help_text=_("internal name for management purposes"),
    )
    internal_remarks = models.TextField(
        _("internal remarks"),
        help_text=_(
            "Remarks or intentions about the form. Can also be used to save notes"
            " for later use or for another admin user."
        ),
        blank=True,
    )

    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        "forms.Category", null=True, blank=True, on_delete=models.PROTECT
    )
    theme = models.ForeignKey(
        "config.Theme",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("form theme"),
        help_text=_(
            "Apply a specific appearance configuration to the form. If left blank, "
            "then the globally configured default is applied."
        ),
    )
    translation_enabled = models.BooleanField(_("translation enabled"), default=False)

    # payments
    payment_backend = PaymentBackendChoiceField(_("payment backend"), blank=True)
    payment_backend_options = models.JSONField(
        _("payment backend options"), default=dict, blank=True, null=True
    )
    # XXX a Foreign Key to FormVariable would be nicer, but we can't do this yet since
    # the frontend saves the variables *after* the form record itself is saved.
    price_variable_key = models.TextField(
        _("price variable key"),
        blank=True,
        help_text=_(
            "Key of the variable that contains the calculated submission price."
        ),
        validators=[variable_key_validator],
    )

    # authentication
    auto_login_authentication_backend = models.CharField(
        _("automatic login"), max_length=UNIQUE_ID_MAX_LENGTH, blank=True
    )
    auth_backends: BaseManager["FormAuthenticationBackend"]

    # appointments
    is_appointment = models.BooleanField(
        _("appointment enabled"),
        default=False,
        help_text=_(
            "Mark the form as an appointment form. "
            "Appointment forms do not support form designer steps."
        ),
    )

    # submission
    submission_limit = models.PositiveIntegerField(
        _("maximum allowed submissions"),
        null=True,
        blank=True,
        help_text=_(
            "Maximum number of allowed submissions per form. Leave this empty if no limit is needed."
        ),
    )
    submission_counter = models.PositiveIntegerField(
        _("submissions counter"),
        default=0,
        help_text=_(
            "Counter to track how many submissions have been completed for the specific form. "
            "This works in combination with the maximum allowed submissions per form and can be "
            "reset via the frontend."
        ),
    )
    submission_confirmation_template = HTMLField(
        _("submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data. If not specified, the global template will be used."
        ),
        blank=True,
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )
    submission_allowed = models.CharField(
        _("submission allowed"),
        choices=SubmissionAllowedChoices.choices,
        default=SubmissionAllowedChoices.yes,
        help_text=_(
            "Whether the user is allowed to submit this form or not, "
            "and whether the overview page should be shown if they are not."
        ),
        max_length=100,
    )
    suspension_allowed = models.BooleanField(
        _("suspension allowed"),
        default=True,
        help_text=_("Whether the user is allowed to suspend this form or not."),
    )
    show_progress_indicator = models.BooleanField(
        _("show progress indicator"),
        default=True,
        help_text=_(
            "Whether the step progression should be displayed in the UI or not."
        ),
    )
    show_summary_progress = models.BooleanField(
        _("show summary of the progress"),
        default=False,
        help_text=_(
            "Whether to display the short progress summary, indicating the current step "
            "number and total amount of steps."
        ),
    )
    display_main_website_link = models.BooleanField(
        _("display main website link"),
        default=True,
        help_text=_(
            "Display the link to the main website on the submission confirmation page."
        ),
    )
    include_confirmation_page_content_in_pdf = models.BooleanField(
        _("include confirmation page content in PDF"),
        default=True,
        help_text=_("Display the instruction from the confirmation page in the PDF."),
    )
    send_confirmation_email = models.BooleanField(
        _("send confirmation email"),
        help_text=_(
            "Whether a confirmation email should be sent to the end user filling in the form."
        ),
        default=True,
    )
    ask_privacy_consent = models.CharField(
        _("ask privacy consent"),
        max_length=50,
        choices=StatementCheckboxChoices.choices,
        default=StatementCheckboxChoices.global_setting,
        help_text=_(
            "If enabled, the user will have to agree to the privacy policy before submitting a form."
        ),
    )
    ask_statement_of_truth = models.CharField(
        _("ask statement of truth"),
        max_length=50,
        choices=StatementCheckboxChoices.choices,
        default=StatementCheckboxChoices.global_setting,
        help_text=_(
            "If enabled, the user will have to agree that they filled out the form "
            "truthfully before submitting it."
        ),
    )

    # Content displayed to end users
    begin_text = models.CharField(
        _("begin text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed at the start of the form to "
            "indicate the user can begin to fill in the form. "
            "Leave blank to get value from global configuration."
        ),
    )
    previous_text = models.CharField(
        _("previous text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the overview page to "
            "go to the previous step. "
            "Leave blank to get value from global configuration."
        ),
    )
    change_text = models.CharField(
        _("change text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the overview page to "
            "change a certain step. "
            "Leave blank to get value from global configuration."
        ),
    )
    confirm_text = models.CharField(
        _("confirm text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the overview page to "
            "confirm the form is filled in correctly. "
            "Leave blank to get value from global configuration."
        ),
    )
    introduction_page_content = CSPPostProcessedWYSIWYGField(
        HTMLField(
            blank=True,
            verbose_name=_("introduction page"),
            help_text=_(
                "Content for the introduction page that leads to the start page of the "
                "form. Leave blank to disable the introduction page."
            ),
        ),
    )
    explanation_template = CSPPostProcessedWYSIWYGField(
        HTMLField(
            blank=True,
            verbose_name=_("explanation template"),
            help_text=_(
                "Content that will be shown on the start page of the form, below the title and above the log in text."
            ),
        ),
    )

    # life cycle management
    active = models.BooleanField(_("active"), default=False)
    maintenance_mode = models.BooleanField(
        _("maintenance mode"),
        default=False,
        help_text=_(
            "Users will not be able to start the form if it is in maintenance mode."
        ),
    )
    _is_deleted = models.BooleanField(default=False)
    activate_on = models.DateTimeField(
        _("activate on"),
        blank=True,
        null=True,
        help_text=_("Date and time on which the form should be activated."),
    )
    deactivate_on = models.DateTimeField(
        _("deactivate on"),
        blank=True,
        null=True,
        help_text=_("Date and time on which the form should be deactivated."),
    )

    # Data removal
    successful_submissions_removal_limit = models.PositiveIntegerField(
        _("successful submission removal limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days successful submissions of this form will remain before being removed. "
            "Leave blank to use value in General Configuration."
        ),
    )
    successful_submissions_removal_method = models.CharField(
        _("successful submissions removal method"),
        max_length=50,
        blank=True,
        choices=RemovalMethods.choices,
        help_text=_(
            "How successful submissions of this form will be removed after the limit. "
            "Leave blank to use value in General Configuration."
        ),
    )
    incomplete_submissions_removal_limit = models.PositiveIntegerField(
        _("incomplete submission removal limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days incomplete submissions of this form will remain before being removed. "
            "Leave blank to use value in General Configuration."
        ),
    )
    incomplete_submissions_removal_method = models.CharField(
        _("incomplete submissions removal method"),
        max_length=50,
        blank=True,
        choices=RemovalMethods.choices,
        help_text=_(
            "How incomplete submissions of this form will be removed after the limit. "
            "Leave blank to use value in General Configuration."
        ),
    )
    errored_submissions_removal_limit = models.PositiveIntegerField(
        _("errored submission removal limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days errored submissions of this form will remain before being removed. "
            "Leave blank to use value in General Configuration."
        ),
    )
    errored_submissions_removal_method = models.CharField(
        _("errored submission removal limit"),
        max_length=50,
        blank=True,
        choices=RemovalMethods.choices,
        help_text=_(
            "How errored submissions of this form will be removed after the limit. "
            "Leave blank to use value in General Configuration."
        ),
    )
    all_submissions_removal_limit = models.PositiveIntegerField(
        _("all submissions removal limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_(
            "Amount of days when all submissions of this form will be permanently deleted. "
            "Leave blank to use value in General Configuration."
        ),
    )

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        FormManager
    ] = FormManager()

    get_begin_text = literal_getter("begin_text", "form_begin_text")
    get_previous_text = literal_getter("previous_text", "form_previous_text")
    get_change_text = literal_getter("change_text", "form_change_text")
    get_confirm_text = literal_getter("confirm_text", "form_confirm_text")

    class Meta:
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def __str__(self):
        if self._is_deleted:
            return _("{name} (deleted)").format(name=self.admin_name)
        else:
            return self.admin_name

    def get_absolute_url(self):
        return reverse("forms:form-detail", kwargs={"slug": self.slug})

    @property
    def is_available(self) -> bool:
        """
        Check if the form is available to start, continue or complete.

        Soft deleted, deactivated, forms in maintenance mode or forms which have reached the
        submission limit are not available.
        """
        if any(
            (
                self._is_deleted,
                not self.active,
                self.maintenance_mode,
                self.submissions_limit_reached,
            )
        ):
            return False
        return True

    @property
    def submissions_limit_reached(self) -> bool:
        if (limit := self.submission_limit) and limit <= self.submission_counter:
            return True
        return False

    def get_registration_backend_display(self) -> str:
        return (
            ", ".join(
                (
                    backend.name
                    if backend.backend in registration_register
                    else _("{backend} (invalid)").format(backend=backend.name)
                )
                for backend in self.registration_backends.all()
            )
            or "-"
        )

    get_registration_backend_display.short_description = _("registrations")

    def get_payment_backend_display(self):
        if not self.payment_backend:
            return "-"

        choices = dict(payment_register.get_choices())
        return choices.get(
            self.payment_backend,
            _("{backend} (invalid)").format(backend=self.payment_backend),
        )

    get_payment_backend_display.short_description = _("payment backend")

    def get_authentication_backends_display(self):
        if not self.auth_backends.exists():
            return "-"

        choices = dict(authentication_register.get_choices())
        return [
            choices.get(
                backend,
                _("{backend} (invalid)").format(backend=backend),
            )
            for backend in self.auth_backends.values_list("backend", flat=True)
        ]

    get_authentication_backends_display.short_description = _("logins")

    @cached_property
    def has_cosign_enabled(self) -> bool:
        """
        Check if cosign is enabled by checking the presence of a cosign (v2) component.

        We don't return the component itself, as you should use
        :class:`openforms.submissions.cosigning.CosignState` to check the state, which
        can take dynamic logic rules into account.
        """
        for component in self.iter_components():
            if component["type"] == "cosign":
                return True
        return False

    @property
    def login_required(self) -> bool:
        # TODO: check if we have a prefetch cache, otherwise fall back to a simpler
        # query with .exists()
        return any(
            [
                form_step.form_definition.login_required
                for form_step in self.formstep_set.all()
            ]
        )

    @property
    def payment_required(self) -> bool:
        # this will later be more dynamic and determined from oa. the linked Product
        return bool(self.payment_backend and self.product and self.product.price)

    @transaction.atomic
    def copy(self):
        from openforms.emails.models import ConfirmationEmailTemplate

        from .form_variable import FormVariable

        form_steps = self.formstep_set.all().select_related("form_definition")

        # form
        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = _uuid.uuid4()
        copy.internal_name = (
            _("{name} (copy)").format(name=self.internal_name)
            if self.internal_name
            else ""
        )
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.product = self.product
        copy.submission_counter = 0

        # name translations

        # these are handled by modeltranslation library and
        # we want to make sure it's translated for all the available languages
        language_codes = [item[0] for item in settings.LANGUAGES]
        for lang in language_codes:
            with override(lang):
                copy.name = _("{name} (copy)").format(name=self.name)

        copy.save()

        # form steps
        form_step_uuid_mappings: dict[str, str] = {}
        for form_step in form_steps:
            original_uuid = form_step.uuid

            form_step.pk = None
            form_step.uuid = _uuid.uuid4()
            form_step.form = copy

            if not form_step.form_definition.is_reusable:
                copy_form_definition = deepcopy(form_step.form_definition)
                copy_form_definition.pk = None
                copy_form_definition.uuid = _uuid.uuid4()
                copy_form_definition.save()
                form_step.form_definition = copy_form_definition

            form_step_uuid_mappings[str(original_uuid)] = str(form_step.uuid)

            form_step.save()

        # logic rules
        for logic in self.formlogic_set.all().select_related("trigger_from_step"):
            logic.pk = None
            logic.uuid = _uuid.uuid4()
            logic.form = copy

            if logic.trigger_from_step:
                logic.trigger_from_step = logic.form.formstep_set.get(
                    order=logic.trigger_from_step.order
                )

            # make sure we have the new uuids of the copied form steps
            for action in logic.actions:
                # form_step_uuid is not a required field and if provided can be None as well
                if action.get("form_step_uuid"):
                    action["form_step_uuid"] = form_step_uuid_mappings[
                        action["form_step_uuid"]
                    ]

            logic.save()

        # form variables
        FormVariable.objects.create_for_form(copy)
        for variable in self.formvariable_set.filter(
            source=FormVariableSources.user_defined
        ):
            variable.pk = None
            variable.form = copy
            variable.save()

        # confirmation email template
        with suppress(ConfirmationEmailTemplate.DoesNotExist):
            self.confirmation_email_template.pk = None
            self.confirmation_email_template.form = copy
            self.confirmation_email_template.save()

        # registration backends
        for registration_backend in self.registration_backends.all():
            registration_backend.pk = None
            registration_backend.form = copy
            registration_backend.save()

        # authentication backends
        for authentication_backend in self.auth_backends.all():
            authentication_backend.pk = None
            authentication_backend.form = copy
            authentication_backend.save()

        return copy

    def get_keys_for_email_confirmation(self) -> list[str]:
        return_keys = set()
        for form_step in self.formstep_set.select_related("form_definition"):
            for key in form_step.form_definition.get_keys_for_email_confirmation():
                if key:
                    return_keys.add(key)
        return list(return_keys)

    def iter_components(self, recursive=True) -> Iterator[Component]:
        # steps are ordered on the 'order' field because of django-ordered-model through
        # the FormStep.Meta configuration
        for form_step in self.formstep_set.select_related("form_definition"):
            yield from form_step.iter_components(recursive=recursive)

    @transaction.atomic
    def restore_old_version(
        self, form_version_uuid: str, user: User | None = None
    ) -> None:
        from ..utils import import_form_data
        from .form_version import FormVersion

        # we use the window function to find the record with its index in _all_
        # of the form revisions. Note that we cannot call a .get(...) on this result set,
        # as that always spits out the RowNumber==1, while we want to know the index of
        # the record in the _total_ set of revisions (our window, with no partitioning).
        form_versions = self.formversion_set.annotate(
            index=Window(
                expression=RowNumber(), order_by=F("created").asc()
            ),  # oldest version gets lowest row number
        )
        form_versions_mapping = {
            form_version.uuid: form_version for form_version in form_versions
        }
        form_version = form_versions_mapping[form_version_uuid]
        old_version_data = form_version.export_blob

        import_form_data(old_version_data, form_version.form)

        # now create a new FormVersion for this restore as well, tracking those nuances
        # in the description.
        FormVersion.objects.create_for(
            form=self,
            user=user,
            description=_("Restored form version {version} (from {created}).").format(
                version=form_version.index,
                created=form_version.created.isoformat(),
            ),
        )

    @property
    def admin_name(self) -> str:
        return self.internal_name or self.name

    def get_statement_checkbox_required(
        self,
        field_name: Literal["ask_privacy_consent", "ask_statement_of_truth"],
    ) -> bool:
        """
        Check whether a particular statement checkbox is required or not.
        """
        value = getattr(self, field_name)
        if value != StatementCheckboxChoices.global_setting:
            return value == StatementCheckboxChoices.required

        # otherwise, check the global configuration
        config = GlobalConfiguration.get_solo()
        return getattr(config, field_name)

    def activate(self):
        self.active = True
        self.activate_on = None
        self.save(update_fields=["active", "activate_on"])
        logger.debug("forms.form_activated", id=self.pk, name=self.admin_name)

    def deactivate(self):
        self.active = False
        self.deactivate_on = None
        self.save(update_fields=["active", "deactivate_on"])
        logger.debug("forms.form_deactivated", id=self.pk, name=self.admin_name)


class FormsExportQuerySet(DeleteFilesQuerySetMixin, models.QuerySet):
    pass


class FormsExport(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    export_content = PrivateMediaFileField(
        verbose_name=_("export content"),
        upload_to="exports/%Y/%m/%d",
        help_text=_("Zip file containing all the exported forms."),
    )
    datetime_requested = models.DateTimeField(
        verbose_name=_("date time requested"),
        help_text=_("The date and time on which the bulk export was requested."),
        auto_now_add=True,
    )
    user = models.ForeignKey(
        to=User,
        verbose_name=_("user"),
        help_text=_("The user that requested the download."),
        on_delete=models.CASCADE,
    )

    objects = FormsExportQuerySet.as_manager()

    class Meta:
        verbose_name = _("forms export")
        verbose_name_plural = _("forms exports")

    def __str__(self):
        return _("Bulk export requested by %(username)s on %(datetime)s") % {
            "username": self.user.username,
            "datetime": localize(localtime(self.datetime_requested)),
        }
