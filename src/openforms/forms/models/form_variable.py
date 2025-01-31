from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, ClassVar

from django.db import models, transaction
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

from glom import glom

from openforms.formio.utils import (
    component_in_editgrid,
    get_component_datatype,
    get_component_default_value,
    is_layout_component,
    iter_components,
)
from openforms.formio.validators import variable_key_validator
from openforms.prefill.constants import IdentifierRoles
from openforms.typing import JSONObject
from openforms.variables.constants import (
    DATA_TYPE_TO_JSON_SCHEMA,
    FormVariableDataTypes,
    FormVariableSources,
)
from openforms.variables.utils import check_initial_value

from .form_definition import FormDefinition

if TYPE_CHECKING:
    from .form import Form


EMPTY_PREFILL_PLUGIN = Q(prefill_plugin="")
EMPTY_PREFILL_ATTRIBUTE = Q(prefill_attribute="")
EMPTY_PREFILL_OPTIONS = Q(prefill_options={})
USER_DEFINED = Q(source=FormVariableSources.user_defined)


class FormVariableManager(models.Manager["FormVariable"]):
    use_in_migrations = True

    @transaction.atomic
    def create_for_form(self, form: "Form") -> None:
        form_steps = form.formstep_set.select_related("form_definition")

        for form_step in form_steps:
            self.synchronize_for(form_step.form_definition)

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
    prefill_options = models.JSONField(
        _("prefill options"),
        default=dict,
        blank=True,
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

    _json_schema = None

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
                    (
                        EMPTY_PREFILL_PLUGIN
                        & EMPTY_PREFILL_ATTRIBUTE
                        & EMPTY_PREFILL_OPTIONS
                    )
                    | (
                        ~EMPTY_PREFILL_PLUGIN
                        & EMPTY_PREFILL_ATTRIBUTE
                        & ~EMPTY_PREFILL_OPTIONS
                        & USER_DEFINED
                    )
                    | (
                        ~EMPTY_PREFILL_PLUGIN
                        & ~EMPTY_PREFILL_ATTRIBUTE
                        & EMPTY_PREFILL_OPTIONS
                    )
                ),
                name="prefill_config_component_or_user_defined",
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

    @property
    def json_schema(self) -> JSONObject | None:
        return self._json_schema

    @json_schema.setter
    def json_schema(self, value: JSONObject):
        self._json_schema = value

    def as_json_schema(self) -> JSONObject:
        """Return JSON schema of form variable.

        If the schema generation for a formio component fails, fall back to a basic
        schema based on the data type.
        """
        if self.source == FormVariableSources.component:
            from openforms.formio.service import as_json_schema  # circular import

            try:
                component = self.form_definition.configuration_wrapper.component_map[
                    self.key
                ]
                self.json_schema = as_json_schema(component)
            except (AttributeError, KeyError):  # pragma: no cover
                pass

        if self.json_schema is None:
            self.json_schema = deepcopy(DATA_TYPE_TO_JSON_SCHEMA[self.data_type])
            self.json_schema["title"] = self.name

        return self.json_schema

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
