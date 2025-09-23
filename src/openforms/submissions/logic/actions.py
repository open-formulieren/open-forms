from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Self, TypedDict

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

from glom import assign
from json_logic import jsonLogic

from openforms.dmn.service import evaluate_dmn
from openforms.formio.service import FormioConfigurationWrapper, FormioData
from openforms.formio.typing.custom import ChildProperties
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic
from openforms.typing import DataMapping, JSONObject

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

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        if self.component not in configuration:
            return None
        component = configuration[self.component]
        assign(component, self.property, self.value, missing=dict)


class DisableNextAction(ActionOperation):
    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls()

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step._can_submit = False


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

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

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(
            form_step_identifier=action["form_step_uuid"],
        )

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

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"], value=action["action"]["value"])

    def eval(
        self,
        context: FormioData,
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
                identifier_variable = context.get(self.identifier_variable) or ""
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
                        source_data, destination_data, mappings, identifier_variable
                    )
                }

    def eval(
        self,
        context: FormioData,
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

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        return cls(variable=action["variable"])

    def eval(
        self,
        context: FormioData,
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

    @classmethod
    def from_action(cls, action: ActionDict) -> Self:
        dmn_config: DMNConfig = action["action"]["config"]

        return cls(**dmn_config)

    def eval(
        self,
        context: FormioData,
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
