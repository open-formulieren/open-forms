from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict

from openforms.formio.service import FormioConfigurationWrapper
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormVariable
from openforms.typing import JSONObject
from openforms.utils.json_logic import ComponentMeta, introspect_json_logic

from ..models import SubmissionStep
from ..models.submission_step import DirtyData


class ActionDetails(TypedDict):
    type: str
    property: dict
    state: Any
    value: Any


class ActionDict(TypedDict):
    component: str
    variable: str
    form_step: str
    form_step_uuid: str
    action: ActionDetails


def compile_action_operation(action: ActionDict) -> "ActionOperation":
    return ActionOperation.from_action(action)


class ActionOperation:
    @staticmethod
    def from_action(action: ActionDict) -> "ActionOperation":
        action_type = action["action"]["type"]
        cls = ACTION_TYPE_MAPPING[action_type]
        return cls.from_action(action)

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        """
        Implements the side effects of the action operation.
        """
        pass

    def get_action_log_data(
        self,
        component_map: Dict[str, ComponentMeta],
        all_variables: Dict[str, FormVariable],
        initial_data: dict,
    ) -> Optional[JSONObject]:
        """Get action information to log"""
        return None


@dataclass
class PropertyAction(ActionOperation):
    component: str
    property: str
    value: Any

    @classmethod
    def from_action(cls, action: ActionDict) -> "PropertyAction":
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
        component[self.property] = self.value

    def get_action_log_data(
        self,
        component_map: Dict[str, ComponentMeta],
        all_variables: Dict[str, FormVariable],
        initial_data: dict,
    ) -> JSONObject:

        component_meta = component_map.get(self.component)

        # figure out the best possible label
        # 1. fall back to component label if there is a label, else empty string
        # 2. if there is a variable, use the name if it's set, else fall back to
        # component label
        label = component_meta.component.get("label", "") if component_meta else ""
        if self.component in all_variables:
            label = all_variables[self.component].name or label

        return {
            "key": self.component,
            "type_display": LogicActionTypes.get_choice(
                LogicActionTypes.property
            ).label,
            "value": self.property,
            "state": self.value,
            "label": label,
        }


class DisableNextAction(ActionOperation):
    @classmethod
    def from_action(cls, action: ActionDict) -> "DisableNextAction":
        return cls()

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step._can_submit = False

    def get_action_log_data(
        self,
        component_map: Dict[str, ComponentMeta],
        all_variables: Dict[str, FormVariable],
        initial_data: dict,
    ) -> JSONObject:

        return {
            "type_display": LogicActionTypes.get_choice(
                LogicActionTypes.disable_next
            ).label,
        }


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> "StepNotApplicableAction":
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
        submission_step_to_modify._is_applicable = False

        # This clears data in the database to make sure that saved steps which later become
        # not-applicable don't have old data
        submission_step_to_modify.data = {}
        if submission_step_to_modify == step:
            step._is_applicable = False
            step.data = DirtyData({})

    def get_action_log_data(
        self,
        component_map: Dict[str, ComponentMeta],
        all_variables: Dict[str, FormVariable],
        initial_data: dict,
    ) -> JSONObject:
        return {
            "type_display": LogicActionTypes.get_choice(
                LogicActionTypes.step_not_applicable
            ).label,
            "step_name": self.form_step_identifier,
        }


@dataclass
class VariableAction(ActionOperation):
    variable: str
    value: JSONObject

    @classmethod
    def from_action(cls, action: ActionDict) -> "VariableAction":
        return cls(variable=action["variable"], value=action["action"]["value"])

    def get_action_log_data(
        self,
        component_map: Dict[str, ComponentMeta],
        all_variables: Dict[str, FormVariable],
        initial_data: dict,
    ) -> JSONObject:
        # Check if it's a primitive value, which doesn't require introspection
        if not isinstance(self.value, (dict, list)):
            value = self.value
        else:
            action_logic_introspection = introspect_json_logic(
                self.value, component_map, initial_data
            )
            value = action_logic_introspection.as_string()

        return {
            "key": self.variable,
            "type_display": LogicActionTypes.get_choice(
                LogicActionTypes.variable
            ).label,
            "value": value,
        }


ACTION_TYPE_MAPPING = {
    LogicActionTypes.property: PropertyAction,
    LogicActionTypes.disable_next: DisableNextAction,
    LogicActionTypes.step_not_applicable: StepNotApplicableAction,
    LogicActionTypes.variable: VariableAction,
}
