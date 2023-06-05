import uuid as _uuid
from copy import deepcopy
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from privates.fields import PrivateMediaFileField
from rest_framework.reverse import reverse
from tinymce.models import HTMLField

from csp_post_processor.fields import CSPPostProcessedWYSIWYGField
from openforms.authentication.fields import AuthenticationBackendMultiSelectField
from openforms.authentication.registry import register as authentication_register
from openforms.data_removal.constants import RemovalMethods
from openforms.payments.fields import PaymentBackendChoiceField
from openforms.payments.registry import register as payment_register
from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.registrations.fields import RegistrationBackendChoiceField
from openforms.registrations.registry import register as registration_register
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin
from openforms.variables.constants import FormVariableSources

from ..constants import SubmissionAllowedChoices
from .utils import literal_getter

User = get_user_model()


class FormQuerySet(models.QuerySet):
    def live(self):
        return self.filter(active=True, _is_deleted=False)


class FormManager(models.Manager.from_queryset(FormQuerySet)):
    pass


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
    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        "forms.Category", null=True, blank=True, on_delete=models.PROTECT
    )
    translation_enabled = models.BooleanField(_("translation enabled"), default=False)

    # backend integration - which registration to use?
    registration_backend = RegistrationBackendChoiceField(
        _("registration backend"), blank=True
    )
    registration_backend_instance = RegistrationBackendChoiceField(
        _("registration backend instance"), blank=True
    )
    registration_backend_options = models.JSONField(
        _("registration backend options"), default=dict, blank=True, null=True
    )

    payment_backend = PaymentBackendChoiceField(_("payment backend"), blank=True)
    payment_backend_options = models.JSONField(
        _("payment backend options"), default=dict, blank=True, null=True
    )

    authentication_backends = AuthenticationBackendMultiSelectField(
        _("authentication backend(s)"), blank=True
    )
    auto_login_authentication_backend = models.CharField(
        _("automatic login"), max_length=UNIQUE_ID_MAX_LENGTH, blank=True
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

    # Data removal
    successful_submissions_removal_limit = models.PositiveIntegerField(
        _("successful submission removal limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
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
        validators=[MinValueValidator(1)],
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
        validators=[MinValueValidator(1)],
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
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days when all submissions of this form will be permanently deleted. "
            "Leave blank to use value in General Configuration."
        ),
    )
    appointment_enabled = models.BooleanField(
        _("appointment enabled"),
        default=False,
        help_text=_("This is experimental mode for appointments"),
    )

    objects = FormManager()

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

    @property
    def is_available(self) -> bool:
        """
        Soft deleted, deactivated or forms in maintenance mode are not available.
        """
        if any((self._is_deleted, not self.active, self.maintenance_mode)):
            return False
        return True

    def get_absolute_url(self):
        return reverse("forms:form-detail", kwargs={"slug": self.slug})

    def get_api_url(self):
        return reverse("api:form-detail", kwargs={"uuid": self.uuid})

    def get_registration_backend_display(self):
        choices = dict(registration_register.get_choices())
        return choices.get(
            self.registration_backend,
            "-",
        )

    get_registration_backend_display.short_description = _("registration backend")

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
        if not self.authentication_backends:
            return "-"

        choices = dict(authentication_register.get_choices())
        return [
            choices.get(
                auth_backend,
                _("{backend} (invalid)").format(backend=self.authentication_backends),
            )
            for auth_backend in self.authentication_backends
        ]

    get_authentication_backends_display.short_description = _(
        "authentication backend(s)"
    )

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
        from .form_variable import FormVariable

        form_steps = self.formstep_set.all().select_related("form_definition")

        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = _uuid.uuid4()
        copy.name = _("{name} (copy)").format(name=self.name)
        copy.internal_name = (
            _("{name} (copy)").format(name=self.internal_name)
            if self.internal_name
            else ""
        )
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.product = None
        copy.save()

        for form_step in form_steps:
            form_step.pk = None
            form_step.uuid = _uuid.uuid4()
            form_step.form = copy

            if not form_step.form_definition.is_reusable:
                copy_form_definition = deepcopy(form_step.form_definition)
                copy_form_definition.pk = None
                copy_form_definition.uuid = _uuid.uuid4()
                copy_form_definition.save()
                form_step.form_definition = copy_form_definition

            form_step.save()

        for logic in self.formlogic_set.all():
            logic.pk = None
            logic.uuid = _uuid.uuid4()
            logic.form = copy
            logic.save()

        FormVariable.objects.create_for_form(copy)
        for variable in self.formvariable_set.filter(
            source=FormVariableSources.user_defined
        ):
            variable.pk = None
            variable.form = copy
            variable.save()

        return copy

    def get_keys_for_email_confirmation(self) -> List[str]:
        return_keys = set()
        for form_step in self.formstep_set.select_related("form_definition"):
            for key in form_step.form_definition.get_keys_for_email_confirmation():
                if key:
                    return_keys.add(key)
        return list(return_keys)

    def iter_components(self, recursive=True):
        # steps are ordered on the 'order' field because of django-ordered-model through
        # the FormStep.Meta configuration
        for form_step in self.formstep_set.select_related("form_definition"):
            yield from form_step.iter_components(recursive=recursive)

    @transaction.atomic
    def restore_old_version(
        self, form_version_uuid: str, user: Optional[User] = None
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
            "datetime": self.datetime_requested,
        }
