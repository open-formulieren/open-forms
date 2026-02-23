from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from itertools import chain
from typing import Any, Self, TypedDict

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

from glom import assign
from json_logic import jsonLogic

from openforms.dmn.service import evaluate_dmn
from openforms.formio.service import (
    FormioConfigurationWrapper,
    FormioData,
    process_visibility,
)
from openforms.formio.typing.custom import ChildProperties
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic, FormStep
from openforms.template import extract_variables_used
from openforms.typing import DataMapping, JSONObject
from openforms.utils.json_logic import introspect_json_logic
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.service import resolve_key

from ..models import Submission, SubmissionStep
from ..models.submission_step import DirtyData
from .log_utils import log_errors
from .service_fetching import perform_service_fetch
from ...variables.constants import FormVariableSources


class ActionDetails(TypedDict):
    type: str
    property: dict
    state: Any
    value: Any
    config: dict


class ActionDict(TypedDict):
    uuid: str
    component: str
    variable: str
    form_step: str
    form_step_uuid: str
    action: ActionDetails


def compile_action_operation(action: ActionDict) -> ActionOperation:
    action_type = action["action"]["type"]
    cls = ACTION_TYPE_MAPPING[action_type]  # pyright: ignore[reportArgumentType]
    return cls.from_action(action)


class ActionOperation:
    rule: FormLogic

    @property
    def unresolved_input_variables(self) -> set[str]:
        """
        Set of input variable names that are used in the action.

        Here, "unresolved" refers to the fact that the variable names are extracted
        directly from the action configuration, and might not represent actual available
        form variables.

        Should be overridden in the child class.
        """
        raise NotImplementedError()

    @property
    def unresolved_output_variables(self) -> set[str]:
        """
        Set of output variable names that are used in the action.

        Here, "unresolved" refers to the fact that the variable names are extracted
        directly from the action configuration, and might not represent actual available
        form variables.

        Should be overridden in the child class
        """
        raise NotImplementedError()

    @property
    def steps(self) -> set[FormStep]:
        """
        Relevant step(s) on which this rule should be executed.

        Should be overridden in the child class.
        """
        raise NotImplementedError()

    def _get_steps(self, keys: Iterable[str]) -> set[FormStep]:
        """
        Get the form steps for unresolved variable keys.

        :param keys: Iterable of (unresolved) variable keys.
        """
        steps = set()
        for key in keys:
            # If we can't resolve it, the key does not belong to a form variable.
            # However, it might be a layout component, so we try to resolve a step for
            # it anyway.
            resolved_key = (
                resolve_key(key, self.rule.form.all_form_variable_keys) or key
            )

            step = self.rule.form.get_form_step(resolved_key)
            if step:
                steps.add(step)

        return steps

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        """
        Constructor from an ActionDict
        """
        raise NotImplementedError()

    def get_require_backend(self) -> bool:
        """
        Get a flag that indicates whether this action requires the backend to be
        evaluated.
        :return: ``True`` if this action requires backend, ``False`` otherwise.
        """
        raise NotImplementedError()

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        """
        Implements the side effects of the action operation.
        """
        pass

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping | None:
        """
        Return a mapping [name/path -> new_value] with changes that are to be
        applied to the context.
        """
        pass


@dataclass
class PropertyAction(ActionOperation):
    component: str
    property_name: str
    value: Any

    @property
    def unresolved_input_variables(self) -> set[str]:
        return set()

    @property
    def unresolved_output_variables(self) -> set[str]:
        # Also need to include children, as it might be a layout component.
        return {self.component} | self.rule.form.get_child_component_keys(
            self.component
        )

    @property
    def steps(self) -> set[FormStep]:
        return self._get_steps(self.unresolved_output_variables)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            component=action["component"],
            property_name=action["action"]["property"]["value"],
            value=action["action"]["state"],
        )

    def get_require_backend(self) -> bool:
        return False

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        # handled directly inside eval
        if self.property_name == "hidden":
            return None
        if self.component not in configuration:
            return None
        component = configuration[self.component]
        assign(component, self.property_name, self.value, missing=dict)

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping | None:
        # To avoid doing unnecessary work, only apply clear-on-hide logic for components
        # for which their action touches the "hidden" property.
        if self.property_name != "hidden":
            return None

        # we now know that we're making the component visible or hidden, but we're not
        # guaranteed that we're actually changing the visibility state at all! For that
        # we need to check at the current component configuration, and that requires
        # first checking if the component is in the current step's configuration. The
        # component *can* be absent if it refers to a component in another step than
        # the one we are currently evaluating. We don't have to do
        # anything in this case, because the clear-on-hide behaviour of that
        # component will be handled once the user has reached that step.
        if self.component not in configuration:
            return None

        component = configuration[self.component]
        should_be_hidden = self.value is True

        # apply the state mutation immediately, so that it's visible to follow up
        # actions and rules operating on the same component. This obsoletes the
        # apply method/side-effects.
        component[self.property_name] = self.value

        # Process the visibility of the component. We want to process the component
        # itself, not try to iterate over its children, so we create a 'fake'
        # configuration. Mutations are performed on the context directly.
        process_visibility(
            {"components": [component]},
            context,
            configuration,
            initial_data=initial_data,
            parent_hidden=should_be_hidden,
            original_input_data=original_input_data,
        )
        return None


@dataclass
class DisableNextAction(ActionOperation):
    form_step_identifier: str

    @property
    def unresolved_input_variables(self) -> set[str]:
        return set()

    @property
    def unresolved_output_variables(self) -> set[str]:
        # This action does not affect any data, so we return an empty set here
        return set()

    @property
    def steps(self) -> set[FormStep]:
        return {self.rule.form.formstep_set.get(uuid=self.form_step_identifier)}

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(form_step_identifier=action["form_step_uuid"])

    def get_require_backend(self) -> bool:
        return False

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        assert step.form_step is not None
        if str(step.form_step.uuid) == self.form_step_identifier:
            step.can_submit = False


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @property
    def unresolved_input_variables(self) -> set[str]:
        return set()

    @property
    def unresolved_output_variables(self) -> set[str]:
        # Note that returning variables here is not fully necessary from a determining-
        # rule-order perspective, as rules related to this step will never get executed
        # anyway if it was marked at not applicable.
        # Together with detecting "self cycles" in the dependency graph, though, we can
        # detect if the rule uses a field from the current step as input, which would be
        # a weird thing to do.
        form_step = self.rule.form.formstep_set.get(uuid=self.form_step_identifier)
        configuration = form_step.form_definition.configuration_wrapper
        return set(configuration.component_map.keys())

    @property
    def steps(self) -> set[FormStep]:
        return self._get_steps(self.rule.unresolved_input_variables_from_trigger)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(form_step_identifier=action.get("form_step_uuid", ""))

    def get_require_backend(self) -> bool:
        # TODO-5962: for now, could decide to split up the database action from marking
        #  a step not applicable. We probably need to return "patch actions" to the
        #  frontend for this to be feasible, because it now relies on
        #  `check_submission_logic` to be run before serialization of the submission
        return True

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        execution_state = (
            step.submission.load_execution_state()
        )  # typically cached already
        submission_step_to_modify = execution_state.resolve_step(
            self.form_step_identifier
        )
        submission_step_to_modify.is_applicable = False

        # This clears data in the database to make sure that saved steps which later become
        # not-applicable don't have old data
        submission_step_to_modify.data = FormioData()
        if submission_step_to_modify == step:
            step.is_applicable = False
            step.data = DirtyData(FormioData())


@dataclass
class StepApplicableAction(ActionOperation):
    form_step_identifier: str

    @property
    def unresolved_input_variables(self) -> set[str]:
        return set()

    @property
    def unresolved_output_variables(self) -> set[str]:
        # Note that returning variables here is not fully necessary from a determining-
        # rule-order perspective, marking a step applicable will not mutate any
        # submission data.
        # Together with detecting "self cycles" in the dependency graph, though, we can
        # detect if the rule uses a field from the current step as input, which would be
        # a weird thing to do.
        form_step = self.rule.form.formstep_set.get(uuid=self.form_step_identifier)
        configuration = form_step.form_definition.configuration_wrapper
        return set(configuration.component_map.keys())

    @property
    def steps(self) -> set[FormStep]:
        return self._get_steps(self.rule.unresolved_input_variables_from_trigger)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

    def get_require_backend(self) -> bool:
        # TODO-5962: see note on step not applicable action
        return True

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        execution_state = (
            step.submission.load_execution_state()
        )  # typically cached already
        submission_step_to_modify = execution_state.resolve_step(
            self.form_step_identifier
        )
        submission_step_to_modify.is_applicable = True


@dataclass
class VariableAction(ActionOperation):
    variable: str
    value: JSONObject

    @property
    def unresolved_input_variables(self) -> set[str]:
        # The value can be a JSON logic expression that takes other variables and
        # performs operations on them. This means we need to introspect it to find
        # variable names.
        return {var.key for var in introspect_json_logic(self.value).get_input_keys()}  # pyright: ignore[reportArgumentType]

    @property
    def unresolved_output_variables(self) -> set[str]:
        return {self.variable}

    @property
    def steps(self) -> set[FormStep]:
        steps = self._get_steps(self.unresolved_output_variables)
        if steps:
            return steps

        # If we cannot resolve a step from the output variables (we are setting a value
        # on a user-defined variable), try to resolve it from the input variables.
        return self._get_steps(
            self.rule.unresolved_input_variables_from_trigger
            | self.unresolved_input_variables
        )

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"], value=action["action"]["value"])

    def get_require_backend(self) -> bool:
        # Note: unfortunately, we cannot temporarily set user-defined variables in the
        # frontend, and only update the backend upon step submit. If there is another
        # rule that uses this user-defined variable as an input, we will be working with
        # outdated values. The backend will have already created a cached version of
        # this rule, with the value that this user-defined variable has at the start of
        # the submission step.
        # TODO-5962: probably need to speed up data access here, as this is now called
        #  dynamically. This analysis could be performed when saving the logic rules.
        output_is_user_defined = self.rule.form.formvariable_set.filter(
            source=FormVariableSources.user_defined,
            key__in=self.unresolved_output_variables,
        ).exists()
        # If the output is a user-defined variable, we require the backend
        return output_is_user_defined

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping:
        with log_errors(self.value, self.rule):
            return {self.variable: jsonLogic(self.value, context.data)}


class DataMappingsConfig(TypedDict):
    property: str
    component_key: str


class DataConfig(TypedDict):
    source_variable: str
    destination_variable: str
    identifier_variable: str
    data_mappings: list[DataMappingsConfig]


@dataclass
class SynchronizeVariablesAction(ActionOperation):
    source_variable: str
    destination_variable: str
    identifier_variable: str
    data_mappings: list[DataMappingsConfig]

    @property
    def unresolved_input_variables(self) -> set[str]:
        # Note that ``data_mappings`` maps properties from the data corresponding to
        # the source variable to the data corresponding to the destination variable,
        # so it's not necessary to include them here. They are always children of the
        # source and destination variable keys.
        return {self.source_variable}

    @property
    def unresolved_output_variables(self) -> set[str]:
        # Note that ``data_mappings`` maps properties from the data corresponding to
        # the source variable to the data corresponding to the destination variable,
        # so it's not necessary to include them here. They are always children of the
        # source and destination variable keys.
        return {self.destination_variable}

    @property
    def steps(self) -> set[FormStep]:
        # Note that at the time of writing this, it is not possible to use a
        # user-defined variable as a destination variable. This means we do not have to
        # fall back to resolving a step from the input (trigger) variables.
        return self._get_steps(self.unresolved_output_variables)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        children_config: DataConfig = action["action"]["config"]  # pyright: ignore[reportAssignmentType]
        return cls(**children_config)

    def get_require_backend(self) -> bool:
        return True

    @staticmethod
    def _map_children_data(
        source_data: Sequence[ChildProperties],
        target_data: Sequence[JSONObject],
        mappings: Sequence[tuple[str, str]],
        identifier_variable: str,
    ) -> Sequence[JSONObject]:
        """
        Map the children to the target variable.

        Each item in the target is expected to have at least the ``bsn`` property to
        be able to match child data.
        """
        # don't mutate the existing target data, but make a copy to replace it
        current_data = deepcopy(target_data)
        result_data_by_identifier = {
            identifier: child
            for child in current_data
            if (identifier := child.get(identifier_variable))
            and isinstance(identifier, str)
        }

        # build up the result based on the selected children, but make sure to keep
        # existing data
        result: Sequence[JSONObject] = []
        for child in source_data:
            # test if the child is unselected - either selection is not enabled which
            # includes all children ("selected" is None), or it is enabled and then
            # included children have "selected" set to "True".
            include_child = child.get("selected") in (None, True)
            if not include_child:
                continue

            # okay, the child should be included. Make sure it's present in the
            # target data. If it already is, keep the existing record as additional
            # fields may already be set.
            mapped_item = result_data_by_identifier.get(child["bsn"])
            if mapped_item is None:
                mapped_item = {target: child[src] for src, target in mappings}
            result.append(mapped_item)

        return result

    def _process_for_component_type(
        self, context: FormioData, component_type: str
    ) -> DataMapping | None:
        match component_type:
            case "children":
                source_data = context.get(self.source_variable, [])
                destination_data = context.get(self.destination_variable) or []
                if not (source_data or destination_data):
                    return None

                # normalize the mapping instructions
                # tuples of (source, target)
                mappings: Sequence[tuple[str, str]] = [
                    (
                        mapping["property"],
                        mapping["component_key"].removeprefix(
                            f"{self.destination_variable}."
                        ),
                    )
                    for mapping in self.data_mappings
                ]

                return {
                    self.destination_variable: self._map_children_data(
                        source_data,
                        destination_data,
                        mappings,
                        self.identifier_variable,
                    )
                }

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping | None:
        configuration = submission.total_configuration_wrapper
        if self.source_variable not in configuration:
            return None

        component_type = configuration[self.source_variable]["type"]
        return self._process_for_component_type(context, component_type)


@dataclass
class ServiceFetchAction(ActionOperation):
    variable: str

    @property
    def unresolved_input_variables(self) -> set[str]:
        var = self.rule.form.formvariable_set.get(key=self.variable)
        fetch_config: ServiceFetchConfiguration = var.service_fetch_configuration

        # The path, query parameters, and header values support templating, so we have
        # to extract the variables from them.
        return {
            variable
            for value in chain(
                fetch_config.query_params.values(),
                fetch_config.headers.values(),
                [fetch_config.path],
            )
            for variable in extract_variables_used(value)
        }

    @property
    def unresolved_output_variables(self) -> set[str]:
        return {self.variable}

    @property
    def steps(self) -> set[FormStep]:
        steps = self._get_steps(self.unresolved_output_variables)
        if steps:
            return steps

        # If we cannot resolve a step from the output variables (we are setting a value
        # on a user-defined variable), try to resolve it from the input variables.
        return self._get_steps(
            self.rule.unresolved_input_variables_from_trigger
            | self.unresolved_input_variables
        )

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"])

    def get_require_backend(self) -> bool:
        # TODO-5692: could depend on the type of input variable. For example, if the
        #  input is a static (authentication) variable, we only have to execute it in
        #  the backend once, because the result won't change the second time.
        return True

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping:
        var = self.rule.form.formvariable_set.get(key=self.variable)
        with log_errors({}, self.rule):  # TODO proper error handling
            result = perform_service_fetch(var, context, str(submission.uuid))
            return {var.key: result.value}


class DMNVariableMapping(TypedDict):
    form_variable: str
    dmn_variable: str


class DMNConfig(TypedDict):
    plugin_id: str
    input_mapping: list[DMNVariableMapping]
    output_mapping: list[DMNVariableMapping]
    decision_definition_id: str
    decision_definition_version: str


@dataclass
class EvaluateDMNAction(ActionOperation):
    input_mapping: list[DMNVariableMapping]
    output_mapping: list[DMNVariableMapping]
    decision_definition_id: str
    plugin_id: str
    decision_definition_version: str = ""
    # DigiD sessions expire after 15 mins of inactivity, so we multiply that a couple
    # times for a long-enought-but-still-soon-expiring cache entry.
    cache_timeout: int = 60 * 15 * 4  # 1 hour

    @property
    def unresolved_input_variables(self) -> set[str]:
        return {item["form_variable"] for item in self.input_mapping}

    @property
    def unresolved_output_variables(self) -> set[str]:
        return {item["form_variable"] for item in self.output_mapping}

    @property
    def steps(self) -> set[FormStep]:
        steps = self._get_steps(self.unresolved_output_variables)
        if steps:
            return steps

        # If we cannot resolve a step from the output variables (we are setting a value
        # on a user-defined variable), try to resolve it from the input variables.
        return self._get_steps(
            self.rule.unresolved_input_variables_from_trigger
            | self.unresolved_input_variables
        )

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        dmn_config: DMNConfig = action["action"]["config"]  # pyright: ignore[reportAssignmentType]

        return cls(**dmn_config)

    def get_require_backend(self) -> bool:
        # TODO-5962: see notes for service fetch action
        return True

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
        initial_data: FormioData,
        *,
        original_input_data: FormioData,
    ) -> DataMapping | None:
        # Mapping from form variables to DMN inputs
        dmn_inputs = {
            item["dmn_variable"]: context[item["form_variable"]]
            for item in self.input_mapping
        }

        def _evaluate_dmn():
            return evaluate_dmn(
                definition_id=self.decision_definition_id,
                version=self.decision_definition_version,
                input_values=dmn_inputs,
                plugin_id=self.plugin_id,
            )

        # Perform DMN call or retrieve result from cache
        inputs = json.dumps(dmn_inputs, cls=DjangoJSONEncoder, sort_keys=True)
        cache_key = hash(
            str(submission.uuid)
            + self.decision_definition_id
            + self.decision_definition_version
            + self.plugin_id
            + inputs
        )
        dmn_outputs = cache.get_or_set(
            cache_key,
            default=_evaluate_dmn,
            timeout=self.cache_timeout,
        )
        assert isinstance(dmn_outputs, dict)

        # Map DMN output to form variables
        return {
            item["form_variable"]: dmn_outputs[item["dmn_variable"]]
            for item in self.output_mapping
            if item["dmn_variable"] in dmn_outputs
        }


@dataclass
class SetRegistrationBackendAction(ActionOperation):
    registration_backend_key: str

    @property
    def unresolved_input_variables(self) -> set[str]:
        return set()

    @property
    def unresolved_output_variables(self) -> set[str]:
        return set()

    @property
    def steps(self) -> set[FormStep]:
        return self._get_steps(self.rule.unresolved_input_variables_from_trigger)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(registration_backend_key=action["action"]["value"])

    def get_require_backend(self) -> bool:
        # TODO-5962: this cannot be executed in the frontend, but we could decide to
        #  exclude it from the analysis, as this action can never influence other
        #  rules/variables
        return True

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step.submission.finalised_registration_backend_key = (
            self.registration_backend_key
        )


ACTION_TYPE_MAPPING: Mapping[LogicActionTypes, type[ActionOperation]] = {
    LogicActionTypes.property: PropertyAction,
    LogicActionTypes.disable_next: DisableNextAction,
    LogicActionTypes.step_not_applicable: StepNotApplicableAction,
    LogicActionTypes.step_applicable: StepApplicableAction,
    LogicActionTypes.variable: VariableAction,
    LogicActionTypes.synchronize_variables: SynchronizeVariablesAction,
    LogicActionTypes.fetch_from_service: ServiceFetchAction,
    LogicActionTypes.evaluate_dmn: EvaluateDMNAction,
    LogicActionTypes.set_registration_backend: SetRegistrationBackendAction,
}
