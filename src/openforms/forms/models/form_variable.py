from typing import TYPE_CHECKING, List

from django.db import models, transaction
from django.db.models import CheckConstraint, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from glom import Path, glom

from openforms.formio.utils import (
    get_component_datatype,
    is_layout_component,
    iter_components,
)

from ..constants import (
    FormVariableDataTypes,
    FormVariableSources,
    FormVariableStaticInitialValues,
)
from .form import Form
from .form_definition import FormDefinition

if TYPE_CHECKING:
    from .form_step import FormStep


def get_now() -> str:
    return timezone.now().isoformat()


STATIC_INITIAL_VALUES = {FormVariableStaticInitialValues.now: get_now}

INITIAL_VALUES = {
    FormVariableDataTypes.string: "",
    FormVariableDataTypes.boolean: "",
    FormVariableDataTypes.object: {},
    FormVariableDataTypes.array: [],
    FormVariableDataTypes.int: "",
    FormVariableDataTypes.float: "",
    FormVariableDataTypes.datetime: "",
    FormVariableDataTypes.time: "",
}


class FormVariableManager(models.Manager):
    @transaction.atomic
    def create_for_form(self, form: "Form") -> None:
        form_steps = form.formstep_set.select_related("form_definition")

        for form_step in form_steps:
            # TODO deal with duplicate keys!
            self.create_for_formstep(form_step)

    def create_for_formstep(self, form_step: "FormStep") -> List["FormVariable"]:
        form_definition_configuration = form_step.form_definition.configuration
        component_keys = [
            component["key"]
            for component in iter_components(
                configuration=form_definition_configuration, recursive=True
            )
        ]
        existing_form_variables_keys = form_step.form.formvariable_set.filter(
            key__in=component_keys,
            form_definition=form_step.form_definition,
        ).values_list("key", flat=True)

        form_variables = []
        for component in iter_components(
            configuration=form_definition_configuration, recursive=True
        ):
            if (
                is_layout_component(component)
                or component["key"] in existing_form_variables_keys
            ):
                continue

            form_variables.append(
                self.model(
                    form=form_step.form,
                    form_definition=form_step.form_definition,
                    prefill_plugin=glom(
                        component,
                        Path("prefill", "plugin"),
                        default="",
                        skip_exc=KeyError,
                    ),
                    prefill_attribute=glom(
                        component,
                        Path("prefill", "attribute"),
                        default="",
                        skip_exc=KeyError,
                    ),
                    key=component["key"],
                    is_sensitive_data=component.get("isSensitiveData", False),
                    source=FormVariableSources.component,
                    data_type=get_component_datatype(component),
                )
            )

        return self.bulk_create(form_variables)


class FormVariable(models.Model):
    form = models.ForeignKey(
        to=Form,
        verbose_name=_("form"),
        help_text=_("Form to which this variable is related"),
        on_delete=models.CASCADE,
    )
    form_definition = models.ForeignKey(
        to=FormDefinition,
        verbose_name=_("form definition"),
        help_text=_(
            "Form definition to which this variable is related. This is kept as metadata"
        ),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("Name of the variable"),
        max_length=100,
    )
    key = models.SlugField(
        verbose_name=_("key"),
        help_text=_("Key of the variable, should be unique with the form."),
        max_length=100,
    )
    source = models.CharField(
        verbose_name=_("source"),
        help_text=_(
            "Where will the data that will be associated with this variable come from"
        ),
        choices=FormVariableSources.choices,
        max_length=50,
    )
    prefill_plugin = models.CharField(
        verbose_name=_("prefill plugin"),
        help_text=_("Which, if any, prefill plugin should be used"),
        blank=True,
        max_length=50,
    )
    prefill_attribute = models.CharField(
        verbose_name=_("prefill attribute"),
        help_text=_(
            "Which attribute from the prefill response should be used to fill this variable"
        ),
        blank=True,
        max_length=50,
    )
    data_type = models.CharField(
        verbose_name=_("data type"),
        help_text=_("The type of the value that will be associated with this variable"),
        choices=FormVariableDataTypes.choices,
        max_length=50,
    )
    data_format = models.CharField(
        verbose_name=_("data format"),
        help_text=_(
            "The format of the value that will be associated with this variable"
        ),
        blank=True,
        max_length=250,
    )
    is_sensitive_data = models.BooleanField(
        verbose_name=_("is sensitive data"),
        help_text=_("Will this variable be associated with sensitive data?"),
        default=False,
    )
    initial_value = models.JSONField(
        verbose_name=_("initial value"),
        help_text=_("The initial value for this field"),
        blank=True,
        null=True,
    )

    objects = FormVariableManager()

    class Meta:
        verbose_name = _("Form variable")
        verbose_name_plural = _("Form variables")
        unique_together = ("form", "key")

        constraints = [
            CheckConstraint(
                check=Q(
                    (Q(prefill_plugin="") & Q(prefill_attribute=""))
                    | (~Q(prefill_plugin="") & ~Q(prefill_attribute=""))
                ),
                name="prefill_config_empty_or_complete",
            )
        ]

    def __str__(self):
        return _("Form variable %(name)s") % {"name": self.name}

    def get_initial_value(self):
        if self.source == FormVariableSources.static:
            return STATIC_INITIAL_VALUES[self.initial_value]()
        else:
            return self.initial_value or INITIAL_VALUES[self.data_type]
