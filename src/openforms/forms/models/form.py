import json
import uuid as _uuid
from copy import deepcopy
from typing import List

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from tinymce.models import HTMLField

from openforms.utils.fields import StringUUIDField

from ...authentication.fields import AuthenticationBackendMultiSelectField
from ...payments.fields import PaymentBackendChoiceField
from ...registrations.fields import RegistrationBackendChoiceField
from .utils import literal_getter


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

    # TODO Refactor to avoid code duplication in src/openforms/forms/utils.py
    @transaction.atomic
    def restore_old_version(self, form_version_uuid: str) -> None:
        from ..api import serializers as api_serializers
        from .form_definition import FormDefinition
        from .form_step import FormStep
        from .form_version import FormVersion

        form_version = FormVersion.objects.get(uuid=form_version_uuid)

        old_version_data = form_version.export_blob

        # Create a form definition with the old version data
        created_form_definitions = []
        for form_definition_data in json.loads(old_version_data["formDefinitions"]):
            form_definition_serializer = api_serializers.FormDefinitionSerializer(
                data=form_definition_data
            )

            try:
                form_definition_serializer.is_valid(raise_exception=True)
                new_fd = form_definition_serializer.save()
                created_form_definitions.append(new_fd)
            except ValidationError as e:
                if "slug" in e.detail and e.detail["slug"][0].code == "unique":
                    existing_fd = FormDefinition.objects.get(
                        slug=form_definition_data["slug"]
                    )
                    existing_fd_hash = existing_fd.get_hash()
                    imported_fd_hash = FormDefinition(
                        configuration=form_definition_data["configuration"]
                    ).get_hash()

                    if existing_fd_hash == imported_fd_hash:
                        # The form definition that is being imported
                        # is identical to the existing form definition
                        # with the same slug, use existing instead
                        # of creating new definition
                        created_form_definitions.append(existing_fd)
                    else:
                        # The imported form definition configuration
                        # is different, create a new form definition
                        form_definition_data.pop("url")
                        form_definition_data.pop("uuid")
                        # This takes care of creating a unique slug
                        new_fd = FormDefinition(**form_definition_data)
                        new_fd.save()
                        created_form_definitions.append(new_fd)
                else:
                    raise e

        # Update the form with the old data
        form_data = json.loads(old_version_data["forms"])[0]
        form_serializer = api_serializers.FormSerializer(data=form_data, instance=self)
        form_serializer.is_valid(raise_exception=True)
        form_serializer.save()

        # Replace form steps to link the form to the new form definitions
        FormStep.objects.filter(form=self).delete()
        form_steps = []
        for form_definition in created_form_definitions:
            form_steps.append(FormStep(form=self, form_definition=form_definition))
        FormStep.objects.bulk_create(form_steps)


class FormLogic(models.Model):
    form_step = models.ForeignKey(
        to="forms.FormStep",
        on_delete=models.CASCADE,
        help_text=_("Form step to which the JSON logic applies."),
    )
    json_logic_trigger = JSONField(
        verbose_name=_("JSON logic"),
        help_text=_("JSON logic associated with a step in a form."),
    )
    component = models.CharField(
        verbose_name=_("component"),
        help_text=_(
            "Formio key of the component in the step to which the logic applies."
        ),
        max_length=100,
    )
    actions = ArrayField(
        JSONField(default=dict),
        verbose_name=_("actions"),
        help_text=_("What action to perform if the JSON logic evaluates to true."),
    )
