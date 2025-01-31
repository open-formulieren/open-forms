from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, ClassVar

from django.db import models, transaction
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

from glom import Path, glom

from openforms.formio.utils import (
    component_in_editgrid,
    get_component_datatype,
    get_component_default_value,
    is_layout_component,
    iter_components,
)
from openforms.formio.validators import variable_key_validator
from openforms.prefill.constants import IdentifierRoles
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.utils import check_initial_value

from .form_definition import FormDefinition

if TYPE_CHECKING:
    from .form import Form
    from .form_step import FormStep


class FormVariableManager(models.Manager):
    use_in_migrations = True

    @transaction.atomic
    def create_for_form(self, form: "Form") -> None:
        form_steps = form.formstep_set.select_related("form_definition")

        for form_step in form_steps:
            self.synchronize_for(form_step.form_definition)

    def create_for_formstep(self, form_step: FormStep) -> list[FormVariable]:
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
                or component["type"] == "content"
                or component["key"] in existing_form_variables_keys
                or component_in_editgrid(form_definition_configuration, component)
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
                    )
                    or "",
                    prefill_attribute=glom(
                        component,
                        Path("prefill", "attribute"),
                        default="",
                        skip_exc=KeyError,
                    )
                    or "",
                    prefill_identifier_role=glom(
                        component,
                        Path("prefill", "identifierRole"),
                        default=IdentifierRoles.main,
                        skip_exc=KeyError,
                    ),
                    key=component["key"],
                    name=component.get("label") or component["key"],
                    is_sensitive_data=component.get("isSensitiveData", False),
                    source=FormVariableSources.component,
                    data_type=get_component_datatype(component),
                    initial_value=get_component_default_value(component),
                )
            )

        return self.bulk_create(form_variables)

    @transaction.atomic
    def synchronize_for(self, form_definition: FormDefinition):
        """
        Synchronize the form variables for a given form definition.

        This creates, updates and/or removes form variables related to the provided
        :class:`FormDefinition` instance. It needs to be called whenever the Formio
        configuration of a form definition is changed so that our form variables in each
        form making use of the form definition accurately reflect the configuration.

        Note that we *don't* remove variables related to other form definitions, as
        multiple isolated transactions for different form definitions can happen at the
        same time.
        """
        # Build the desired state
        desired_variables: list[FormVariable] = []
        # XXX: looping over the configuration_wrapper is not (yet) viable because it
        # also yields the components nested inside edit grids, which we need to ignore.
        # So, we stick to iter_components. Performance wise this should be okay since we
        # only need to do one pass.
        configuration = form_definition.configuration
        for component in iter_components(configuration=configuration, recursive=True):
            # we need to ignore components that don't actually hold any values - there's
            # no point to create variables for those.
            if is_layout_component(component):
                continue
            if component["type"] in ("content", "softRequiredErrors"):
                continue
            if component_in_editgrid(configuration, component):
                continue

            # extract options from the component
            prefill_plugin = glom(component, "prefill.plugin", default="") or ""
            prefill_attribute = glom(component, "prefill.attribute", default="") or ""
            prefill_identifier_role = glom(
                component, "prefill.identifierRole", default=IdentifierRoles.main
            )

            desired_variables.append(
                self.model(
                    form=None,  # will be set later when visiting all affected forms
                    key=component["key"],
                    form_definition=form_definition,
                    prefill_plugin=prefill_plugin,
                    prefill_attribute=prefill_attribute,
                    prefill_identifier_role=prefill_identifier_role,
                    name=component.get("label") or component["key"],
                    is_sensitive_data=component.get("isSensitiveData", False),
                    source=FormVariableSources.component,
                    data_type=get_component_datatype(component),
                    initial_value=get_component_default_value(component),
                )
            )

        desired_keys = [variable.key for variable in desired_variables]

        # if the Formio configuration of the form definition itself is updated and
        # components have been removed or their keys have changed, we know for certain
        # we can discard those old form variables - it doesn't matter which form they
        # belong to.
        stale_variables = self.filter(form_definition=form_definition).exclude(
            key__in=desired_keys
        )
        stale_variables.delete()

        # check which form (steps) are affected and patch them up. It is irrelevant whether
        # the form definition is re-usable or not, though semantically at most one form step
        # should be found for single-use form definitions.
        # fmt: off
        affected_form_steps = (
            form_definition
            .formstep_set # pyright: ignore[reportAttributeAccessIssue]
            .select_related("form")
        )
        # fmt: on

        # Finally, collect all the instances and efficiently upsert them - creating missing
        # variables and updating existing variables in a single query.
        to_upsert: list[FormVariable] = []
        for step in affected_form_steps:
            for variable in desired_variables:
                form_specific_variable = deepcopy(variable)
                form_specific_variable.form = step.form
                to_upsert.append(form_specific_variable)

        self.bulk_create(
            to_upsert,
            # enables UPSERT behaviour so that existing records get updated and missing
            # records inserted
            update_conflicts=True,
            update_fields=(
                "prefill_plugin",
                "prefill_attribute",
                "prefill_identifier_role",
                "name",
                "is_sensitive_data",
                "source",
                "data_type",
                "initial_value",
            ),
            unique_fields=("form", "key"),
        )


class FormVariable(models.Model):
    form = models.ForeignKey(
        to="Form",
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
    name = models.TextField(
        verbose_name=_("name"),
        help_text=_("Name of the variable"),
    )
    key = models.TextField(
        verbose_name=_("key"),
        help_text=_("Key of the variable, should be unique with the form."),
        validators=[variable_key_validator],
    )
    source = models.CharField(
        verbose_name=_("source"),
        help_text=_(
            "Where will the data that will be associated with this variable come from"
        ),
        choices=FormVariableSources.choices,
        max_length=50,
    )
    service_fetch_configuration = models.ForeignKey(
        verbose_name=_("service fetch configuration"),
        to="variables.ServiceFetchConfiguration",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
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
        max_length=200,
    )
    prefill_identifier_role = models.CharField(
        verbose_name=_("prefill identifier role"),
        help_text=_(
            "In case that multiple identifiers are returned (in the case of eHerkenning bewindvoering and DigiD "
            "Machtigen), should the prefill data related to the main identifier be used, or that related to the authorised person?"
        ),
        choices=IdentifierRoles.choices,
        default=IdentifierRoles.main,
        max_length=100,
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

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        FormVariableManager
    ] = FormVariableManager()

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
            ),
            CheckConstraint(
                check=~Q(
                    (~Q(prefill_plugin=""))
                    & Q(service_fetch_configuration__isnull=False)
                ),
                name="prefill_config_xor_service_fetch_config",
            ),
            CheckConstraint(
                check=Q(
                    (
                        Q(form_definition__isnull=True)
                        & ~Q(source=FormVariableSources.component)
                    )
                    | Q(form_definition__isnull=False)
                ),
                name="form_definition_not_null_for_component_vars",
            ),
        ]

    def __str__(self):
        return _("Form variable '{key}'").format(key=self.key)

    def get_initial_value(self):
        return self.initial_value

    def derive_info_from_component(self):
        if self.source != FormVariableSources.component or not self.form_definition:
            return

        config_wrapper = self.form_definition.configuration_wrapper
        component = config_wrapper.component_map.get(self.key)

        if self.initial_value is None:
            self.initial_value = get_component_default_value(component)

        self.data_type = get_component_datatype(component)

    def check_data_type_and_initial_value(self):
        self.derive_info_from_component()

        if self.source == FormVariableSources.user_defined:
            self.initial_value = check_initial_value(self.initial_value, self.data_type)

    def save(self, *args, **kwargs):
        self.check_data_type_and_initial_value()

        super().save(*args, **kwargs)
