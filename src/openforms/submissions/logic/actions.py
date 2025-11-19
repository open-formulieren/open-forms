from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
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
from openforms.forms.models import FormLogic
from openforms.forms.models.logic import _resolve_key
from openforms.template import extract_variables_used
from openforms.typing import DataMapping, JSONObject
from openforms.utils.json_logic import introspect_json_logic

from ..models import Submission, SubmissionStep
from ..models.submission_step import DirtyData
from .log_utils import log_errors
from .service_fetching import perform_service_fetch


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
    cls = ACTION_TYPE_MAPPING[action_type]
    return cls.from_action(action)


class ActionOperation:
    rule: FormLogic

    # TODO-2409: if there are no input/output variables, return None instead?
    # TODO-2409: variables might not be an accurate name, as it can also include
    #  component keys
    @property
    def input_variables(self) -> set[str]:
        """Return a set of input variable names that are used in the action."""
        return set()

    @property
    def output_variables(self) -> set[str]:
        """Return a set of output variable names that are used in the action."""
        return set()

    # TODO-2409: another possibility would be to have a (class) property on the Action
    #  that defines which variables should be used to determine the step. Can be an
    #  enum with options "json_logic_trigger", "input_variables", "output_variables".
    #  Though we might also need a way to indicate it needs to be executed on all steps?
    #  Don't think this is a good idea actually. Suppose you want to add another
    #  ActionOperation with a new way to determine the step. Then you'd need to
    #  implement that behaviour inside the FormLogic model, which isn't really
    #  clear directly. We are doing a lot of things that the FormLogic model should do
    #  though. Not really sure about this one
    def get_steps(self):
        """Get the relevant step(s) on which this rule should be executed."""
        return set()
        raise NotImplementedError()

    def _get_steps(self, keys: set[str]):
        steps = set()
        for key in keys:
            # If we can't resolve it, the key does not belong to a form variable.
            # HOWEVER, it might be a component, so we try to resolve a step for it
            # anyway.
            resolved_key = _resolve_key(key, self.rule.form.all_form_variables) or key

            step = self.rule.form.get_form_step(resolved_key)
            if step:
                steps.add(step)

        return steps

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        """
        Constructor from an ActionDict
        """
        pass

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
    ) -> DataMapping | None:
        """
        Return a mapping [name/path -> new_value] with changes that are to be
        applied to the context.
        """
        pass


@dataclass
class PropertyAction(ActionOperation):
    component: str
    property: str
    value: Any

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            component=action["component"],
            property=action["action"]["property"]["value"],
            value=action["action"]["state"],
        )

    @property
    def output_variables(self) -> set[str]:
        """Return a set of output variable names that are used in the action."""
        # TODO-2409: is it worth only returning this for the "hidden" property action,
        #  as marking a field as "required" or "disabled" doesn't affect the data?
        # Also need to include children, as it might be a layout component. Note that
        # these include all component keys, and should still be resolved against the
        # available form variables
        return {self.component} | self.rule.form.get_child_component_keys(
            self.component
        )

    def get_steps(self):
        return self._get_steps(self.output_variables)

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        if self.component not in configuration:
            return None
        component = configuration[self.component]
        assign(component, self.property, self.value, missing=dict)

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
    ) -> DataMapping | None:
        # To avoid doing unnecessary work, only apply clear-on-hide logic for components
        # for which their action sets the "hidden" property to True.
        if not (self.property == "hidden" and self.value):
            return None

        # Note that this can happen when the action applies to a component of a
        # different step than we are currently evaluating. We don't have to do
        # anything in this case, because the clear-on-hide behaviour of that
        # component will be handled once the user has reached that step.
        if self.component not in configuration:
            return None

        component = configuration[self.component]

        # Process the visibility of the component. We want to process the component
        # itself, not try to iterate over its children, so we create a 'fake'
        # configuration. Mutations are performed on the context directly.
        process_visibility(
            {"components": [component]}, context, configuration, parent_hidden=True
        )
        return None


class DisableNextAction(ActionOperation):
    # TODO-2409: we cannot add variables at the moment, because we have no context
    #  about which step is involved.
    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls()

    def get_steps(self):
        steps = self._get_steps(self.rule.raw_input_keys)
        # Return last step
        return {max(steps, key=lambda step: step.order)} if steps else steps

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step._can_submit = False


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @property
    def output_variables(self) -> set[str]:
        """Return a set of output variable names that are used in the action."""
        # TODO-2409: once we resolve against all form variables, it will remove all
        #  components that have no variable. Is that OK for this action? Feels like it
        #  might introduce some edge cases. Perhaps worth considering to not resolve
        #  against the variables at all?
        # TODO-2409: do we need to speed up data access here?
        # TODO-2409: ALSO, perhaps this is not even necessary, as we will get all rules
        #  per step anyway. Meaning all other rules related to that step will not get
        #  executed, since we never reach that step. Though it makes sense to include
        #  them from a graph-building perspective. It will be incomplete otherwise.
        form_step = self.rule.form.formstep_set.get(uuid=self.form_step_identifier)
        configuration = form_step.form_definition.configuration_wrapper
        return set(configuration.component_map.keys())

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

    def get_steps(self):
        steps = self._get_steps(self.rule.raw_input_keys)
        # Return last step to make sure all data will be available
        return {max(steps, key=lambda step: step.order)} if steps else steps

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
    def output_variables(self) -> set[str]:
        """Return a set of output variable names that are used in the action."""
        # TODO-2409: see comments on "not applicable" action
        form_step = self.rule.form.formstep_set.get(uuid=self.form_step_identifier)
        configuration = form_step.form_definition.configuration_wrapper
        return set(configuration.component_map.keys())

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

    def get_steps(self):
        steps = self._get_steps(self.rule.raw_input_keys)
        # Return last step to make sure all data will be available
        return {max(steps, key=lambda step: step.order)} if steps else steps

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
    def input_variables(self) -> set[str]:
        """Return a set of input variable names that are used in the action."""

        # The value can be a JSON logic expression that takes other variables and
        # performs operations on them. This means we need to introspect it to find
        # variable names. Note that they should still be resolved against all available
        # form variables.
        return {var.key for var in introspect_json_logic(self.value).get_input_keys()}

    @property
    def output_variables(self) -> set[str]:
        """Return a set of output variable names that are used in the action."""
        return {self.variable}

    def get_steps(self):
        steps = self._get_steps(self.output_variables)
        if steps:
            return steps

        # TODO-2409: ideally we would only do this if there is a user-defined variable
        #  involved, AND we weren't able to determine a step from the other actions on
        #  the corresponding logic rule.
        #  It might be risky to determine the step based on the other actions, as we
        #  have no view on how the user-defined variable is used. E.g. it might be used
        #  in dynamic configuration of radio/select/selectboxes components. Relying on
        #  other actions might result in the wrong step
        # If we cannot resolve a step from the output variables (might be because we are
        # setting a value on a user-defined variable), try to resolve it from the input
        # variables. Select the last step to make sure we have all data
        steps = self._get_steps(self.rule.raw_input_keys | self.input_variables)
        return {max(steps, key=lambda step: step.order)} if steps else steps

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"], value=action["action"]["value"])

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
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
    def input_variables(self) -> set[str]:
        """
        Return a set of input variable names that are used in the action.

        Note that ``data_mappings`` maps properties from the value of source variable to
        the value of destination variable, so it's not necessary to include them here.
        """
        return {self.source_variable}

    @property
    def output_variables(self) -> set[str]:
        """
        Return a set of output variable names that are used in the action.

        Note that ``data_mappings`` maps properties from the value of source variable to
        the value of destination variable, so it's not necessary to include them here.
        """
        return {self.destination_variable}

    def get_steps(self):
        # Note that at the time of writing this, it is not possible to use a
        # user-defined variable as a destination variable.
        return self._get_steps(self.output_variables)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        children_config: DataConfig = action["action"]["config"]
        return cls(**children_config)

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
    def input_variables(self) -> set[str]:
        var = self.rule.form.formvariable_set.get(key=self.variable)
        fetch_config = var.service_fetch_configuration

        # The query parameters and header values support templating, so we have to
        # extract the variables from them.
        return {
            variable
            for value in chain(
                fetch_config.query_params.values(), fetch_config.headers.values()
            )
            for variable in extract_variables_used(value)
        }

    @property
    def output_variables(self) -> set[str]:
        return {self.variable}

    def get_steps(self):
        steps = self._get_steps(self.output_variables)
        if steps:
            return steps

        # If we cannot resolve a step from the output variables (might be because we are
        # setting a value on a user-defined variable), try to resolve it from the input
        # variables. Select the last step to make sure we have all data.
        steps = self._get_steps(self.rule.raw_input_keys | self.input_variables)
        return {max(steps, key=lambda step: step.order)} if steps else steps

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"])

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
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
    def input_variables(self) -> set[str]:
        return {item["form_variable"] for item in self.input_mapping}

    @property
    def output_variables(self) -> set[str]:
        return {item["form_variable"] for item in self.output_mapping}

    def get_steps(self):
        return self._get_steps(self.output_variables)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        dmn_config: DMNConfig = action["action"]["config"]

        return cls(**dmn_config)

    def eval(
        self,
        context: FormioData,
        configuration: FormioConfigurationWrapper,
        submission: Submission,
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

        # Map DMN output to form variables
        return {
            item["form_variable"]: dmn_outputs[item["dmn_variable"]]
            for item in self.output_mapping
            if item["dmn_variable"] in dmn_outputs
        }


@dataclass
class SetRegistrationBackendAction(ActionOperation):
    registration_backend_key: str

    def get_steps(self):
        return self._get_steps(self.rule.raw_input_keys)

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(registration_backend_key=action["action"]["value"])

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
