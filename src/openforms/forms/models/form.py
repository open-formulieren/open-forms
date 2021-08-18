import uuid as _uuid
from copy import deepcopy
from typing import List

from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from rest_framework.reverse import reverse
from tinymce.models import HTMLField

from openforms.utils.fields import StringUUIDField

from ...authentication.fields import AuthenticationBackendMultiSelectField
from ...payments.fields import PaymentBackendChoiceField
from ...registrations.fields import RegistrationBackendChoiceField
from .utils import literal_getter
from ...config.constants import RemovalMethods


class FormQuerySet(models.QuerySet):
    def live(self):
        return self.filter(active=True, _is_deleted=False)


class FormManager(models.Manager.from_queryset(FormQuerySet)):
    pass


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """

    uuid = StringUUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    name = models.CharField(_("name"), max_length=50)
    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.CASCADE
    )

    # backend integration - which registration to use?
    registration_backend = RegistrationBackendChoiceField(
        _("registration backend"), blank=True
    )
    registration_backend_options = JSONField(
        _("registration backend options"), default=dict, blank=True, null=True
    )

    payment_backend = PaymentBackendChoiceField(_("payment backend"), blank=True)
    payment_backend_options = JSONField(
        _("payment backend options"), default=dict, blank=True, null=True
    )

    authentication_backends = AuthenticationBackendMultiSelectField(
        _("authentication backend(s)"), blank=True
    )
    submission_confirmation_template = HTMLField(
        _("submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data. If not specified, the global template will be used."
        ),
        blank=True,
    )
    can_submit = models.BooleanField(
        _("can submit"),
        default=True,
        help_text=_("Whether the user is allowed to submit this form or not."),
    )
    show_progress_indicator = models.BooleanField(
        _("show progress indicator"),
        default=True,
        help_text=_(
            "Whether the step progression should be displayed in the UI or not."
        ),
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

    # life cycle management
    active = models.BooleanField(default=False)
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
        null=True,
        choices=RemovalMethods,
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
        _("registration backend status"),
        max_length=50,
        blank=True,
        null=True,
        choices=RemovalMethods,
        help_text=_(
            "How incomplete submissions of this form will be removed after the limit. "
            "Leave blank to use value in General Configuration."
        ),
    )
    errored_submissions_removal_limit = models.PositiveIntegerField(
        _("errored submission removal days limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days errored submissions of this form will remain before being removed. "
            "Leave blank to use value in General Configuration."
        ),
    )
    errored_submissions_removal_method = models.CharField(
        _("registration backend status"),
        max_length=50,
        blank=True,
        null=True,
        choices=RemovalMethods,
        help_text=_(
            "How errored submissions of this form will be removed after the limit of days. "
            "Leave blank to use value in General Configuration."
        ),
    )
    all_submissions_removal_limit = models.PositiveIntegerField(
        _("errored submission removal days limit"),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Amount of days when all submissions of this form will be permanently deleted. "
            "Leave blank to use value in General Configuration."
        ),
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
        return self.name

    def get_absolute_url(self):
        return reverse("forms:form-detail", kwargs={"slug": self.slug})

    def get_api_url(self):
        return reverse("api:form-detail", kwargs={"uuid": self.uuid})

    @property
    def login_required(self) -> bool:
        return any(
            [
                form_step.form_definition.login_required
                for form_step in self.formstep_set.all()
            ]
        )

    @property
    def payment_required(self) -> bool:
        # this will later be more dynamic and determined from oa. the linked Product
        return bool(
            self.payment_backend
            and self.payment_backend_options
            and self.product
            and self.product.price
        )

    @property
    def first_step(self):
        return self.formstep_set.first().order

    @transaction.atomic
    def copy(self):
        form_steps = self.formstep_set.all()

        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = _uuid.uuid4()
        copy.name = _("{name} (copy)").format(name=self.name)
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.product = None
        copy.save()

        for form_step in form_steps:
            form_step.pk = None
            form_step.uuid = _uuid.uuid4()
            form_step.form = copy
            form_step.save()

        return copy

    def get_keys_for_email_confirmation(self) -> List[str]:
        return_keys = set()
        for form_step in self.formstep_set.select_related("form_definition"):
            for key in form_step.form_definition.get_keys_for_email_confirmation():
                if key:
                    return_keys.add(key)
        return list(return_keys)

    def iter_components(self, recursive=True):
        for form_step in self.formstep_set.select_related("form_definition"):
            yield from form_step.iter_components(recursive=recursive)

    @cached_property
    def has_sensitive_information(self):
        for form_step in self.formstep_set.select_related("form_definition"):
            if form_step.form_definition.has_sensitive_information:
                return True
        return False

    @cached_property
    def sensitive_fields(self):
        sensitive_fields = []
        for form_step in self.formstep_set.select_related("form_definition"):
            sensitive_fields += form_step.form_definition.sensitive_fields
        return sensitive_fields

    @transaction.atomic
    def restore_old_version(self, form_version_uuid: str) -> None:
        from ..utils import import_form_data
        from .form_version import FormVersion

        form_version = FormVersion.objects.get(uuid=form_version_uuid)
        old_version_data = form_version.export_blob

        import_form_data(old_version_data, form_version.form)


class FormLogic(models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        to="forms.Form",
        on_delete=models.CASCADE,
        help_text=_("Form to which the JSON logic applies."),
    )
    json_logic_trigger = JSONField(
        verbose_name=_("JSON logic"),
        help_text=_("JSON logic associated with a step in a form."),
    )
    actions = JSONField(
        verbose_name=_("actions"),
        help_text=_("Which action(s) to perform if the JSON logic evaluates to true."),
    )
