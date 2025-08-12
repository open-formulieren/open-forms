from __future__ import annotations

import itertools
from copy import copy, deepcopy
from typing import ClassVar

from django.db import models, transaction
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

import elasticapm
import structlog

from openforms.formio.utils import (
    get_component_data_subtype,
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

from .form import Form
from .form_definition import FormDefinition

EMPTY_PREFILL_PLUGIN = Q(prefill_plugin="")
EMPTY_PREFILL_ATTRIBUTE = Q(prefill_attribute="")
EMPTY_PREFILL_OPTIONS = Q(prefill_options={})
USER_DEFINED = Q(source=FormVariableSources.user_defined)

DATA_TYPE_ARRAY = Q(data_type=FormVariableDataTypes.array)
EMPTY_DATA_SUBTYPE = Q(data_subtype="")
COMPONENT = Q(source=FormVariableSources.component)

# these are the attributes that are derived from the matching formio component,
# see FormVariableManager.synchronize_for. Other attributes are relational or
# related to user defined variables (like service fetch, prefill options...).
UPSERT_ATTRIBUTES_TO_COMPARE: tuple[str, ...] = (
    "prefill_plugin",
    "prefill_attribute",
    "prefill_identifier_role",
    "name",
    "is_sensitive_data",
    "data_type",
    "initial_value",
)


logger = structlog.stdlib.get_logger(__name__)


class FormVariableManager(models.Manager["FormVariable"]):
    use_in_migrations = True

    @transaction.atomic
    def create_for_form(self, form: Form) -> None:
        form_steps = form.formstep_set.select_related(  # pyright: ignore[reportAttributeAccessIssue]
            "form_definition"
        )

        for form_step in form_steps:
            self.synchronize_for(form_step.form_definition)

    @elasticapm.capture_span(span_type="app.core.models")
    @transaction.atomic(savepoint=False)
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
        desired_keys: set[str] = set()
        # XXX: looping over the configuration_wrapper is not (yet) viable because it
        # also yields the components nested inside edit grids, which we need to ignore.
        # So, we stick to iter_components. We deliberately do a single pass to process
        # the formio definition and then "copy" the information for each affected form
        # so that we can avoid excessive component tree processing.
        configuration = form_definition.configuration
        for component in iter_components(
            configuration=configuration,
            recursive=True,
            # components inside edit grids are not real variables
            recurse_into_editgrid=False,
        ):
            # we need to ignore components that don't actually hold any values - there's
            # no point to create variables for those.
            if is_layout_component(component):
                continue
            if component["type"] in ("content", "softRequiredErrors"):
                continue

            # extract options from the component
            prefill = component.get("prefill", {})
            prefill_plugin = prefill.get("plugin") or ""
            prefill_attribute = prefill.get("attribute") or ""
            prefill_identifier_role = (
                prefill.get("identifierRole") or IdentifierRoles.main
            )

            key = component["key"]
            desired_keys.add(key)
            desired_variables.append(
                self.model(
                    form=None,  # will be set later when visiting all affected forms
                    key=key,
                    form_definition=form_definition,
                    prefill_plugin=prefill_plugin,
                    prefill_attribute=prefill_attribute,
                    prefill_identifier_role=prefill_identifier_role,
                    name=component.get("label") or component["key"],
                    is_sensitive_data=component.get("isSensitiveData", False),
                    source=FormVariableSources.component,
                    data_type=get_component_datatype(component),
                    data_subtype=get_component_data_subtype(component),
                    initial_value=get_component_default_value(component),
                )
            )

        # if the Formio configuration of the form definition itself is updated and
        # components have been removed or their keys have changed, we know for certain
        # we can discard those old form variables - it doesn't matter which form they
        # belong to.
        stale_variables = self.filter(form_definition=form_definition).exclude(
            key__in=desired_keys
        )
        stale_variables.delete()

        # Check which forms are affected and patch them up.
        # It is irrelevant whether
        # the form definition is re-usable or not, though semantically at most one form step
        # should be found for single-use form definitions.
        affected_forms = (
            Form.objects.filter(formstep__form_definition=form_definition)
            .order_by("id")
            .distinct("id")
            .values_list("pk", flat=True)
            .iterator()
        )

        # Collect all the instances and efficiently upsert them - creating missing
        # variables and updating existing variables in a single query.
        to_upsert: list[FormVariable] = []

        # We check which form variables actually need to be updated or inserted. If
        # naively sending everything to the UPSERT we are sending pointless data to
        # Postgres which puts unnecessary load.
        existing_form_variables = (
            self.filter(form_definition=form_definition).order_by("form_id").iterator()
        )
        # keep track of (form_id, form_key) tuples that were considered, so that we can
        # efficiently decide whether we can ignore it or not based on existing variables.
        seen: set[tuple[int, str]] = set()

        # first look at form variables that already exist since we can exclude those
        # from the upsert
        form_variables_by_form = itertools.groupby(
            existing_form_variables, key=lambda fv: fv.form_id
        )
        for form_id, variables in form_variables_by_form:
            assert form_id is not None
            variables_by_key = {variable.key: variable for variable in variables}

            def _add_variable(variable: FormVariable):
                form_specific_variable = copy(variable)
                form_specific_variable.form_id = form_id  # noqa: B023
                to_upsert.append(form_specific_variable)

            # check whether we need to create or update the variable by comparing against
            # existing variables.
            for desired_variable in desired_variables:
                existing_variable = variables_by_key.get(key := desired_variable.key)
                seen.add((form_id, key))

                if existing_variable is None:
                    _add_variable(desired_variable)
                    continue

                # otherwise, check if we need to update or can skip this variable to
                # make the upsert query smaller
                if not existing_variable.matches(desired_variable):
                    # it needs to be updated
                    _add_variable(desired_variable)

        # Finally, process variables that don't exist yet at all
        for form_id in affected_forms:
            for variable in desired_variables:
                _lookup = (form_id, variable.key)
                # it already exists and has been processed
                if _lookup in seen:
                    continue

                # it doesn't exist and needs to be created
                form_specific_variable = copy(variable)
                form_specific_variable.form_id = form_id
                to_upsert.append(form_specific_variable)

        self.bulk_create(
            to_upsert,
            # enables UPSERT behaviour so that existing records get updated and missing
            # records inserted
            update_conflicts=True,
            update_fields=UPSERT_ATTRIBUTES_TO_COMPARE + ("source",),
            unique_fields=("form", "key"),
        )


class FormVariable(models.Model):
    form = models.ForeignKey(
        to="Form",
        verbose_name=_("form"),
        help_text=_("Form to which this variable is related"),
        on_delete=models.CASCADE,
    )
    form_id: int | None
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
    data_subtype = models.CharField(
        verbose_name=_("data subtype"),
        help_text=_(
            "This field represents the data type of the values inside the container "
            "for components that are configured as 'multiple'."
        ),
        choices=FormVariableDataTypes.choices,
        max_length=50,
        blank=True,
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
            CheckConstraint(
                check=(
                    (
                        (DATA_TYPE_ARRAY & ~EMPTY_DATA_SUBTYPE)
                        | (~DATA_TYPE_ARRAY & EMPTY_DATA_SUBTYPE)
                    )
                    & COMPONENT
                )
                | ~COMPONENT,
                name="form_variable_subtype_empty_iff_data_type_is_not_array",
            ),
            CheckConstraint(
                check=~Q(
                    data_type__in=(
                        FormVariableDataTypes.partners,
                        FormVariableDataTypes.editgrid,
                        FormVariableDataTypes.children,
                    )
                ),
                name="form_variable_data_type_is_not_subtype_exclusive",
            ),
        ]

    def __str__(self):
        return _("Form variable '{key}'").format(key=self.key)

    def save(self, *args, **kwargs):
        self.check_data_type_and_initial_value()

        super().save(*args, **kwargs)

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
                assert isinstance(self.json_schema, dict)
            except (AttributeError, KeyError) as exc:  # pragma: no cover
                logger.error(
                    "component_json_schema_generation_failed",
                    key=self.key,
                    exc_info=exc,
                )
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
        self.data_subtype = get_component_data_subtype(component)

    def check_data_type_and_initial_value(self):
        self.derive_info_from_component()

        if self.source == FormVariableSources.user_defined:
            self.initial_value = check_initial_value(self.initial_value, self.data_type)

    def matches(self, other: FormVariable) -> bool:
        """
        Check if the other form variable matches this instance.

        Matching can only be performed on component variables to check if they are
        still in sync. Foreign key relations to form etc. are ignored as this doesn't
        contain semantic information.
        """
        assert self.source == FormVariableSources.component, (
            "Can only compare component variables"
        )
        assert other.source == FormVariableSources.component, (
            "Can only compare component variables"
        )
        assert self.key == other.key, (
            "Different keys are being compared, are you sure you're comparing "
            "the right instances?"
        )

        # these are the attributes that are derived from the matching formio component,
        # see FormVariableManager.synchronize_for. Other attributes are relational or
        # related to user defined variables (like service fetch, prefill options...).
        all_equal = all(
            getattr(self, attr) == getattr(other, attr)
            for attr in UPSERT_ATTRIBUTES_TO_COMPARE
        )
        return all_equal
