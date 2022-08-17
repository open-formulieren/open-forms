from dataclasses import dataclass
from typing import Any, TypedDict

from openforms.formio.utils import get_component
from openforms.forms.constants import LogicActionTypes
from openforms.typing import JSONObject

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
    action: ActionDetails


def compile_action_operation(action: ActionDict):
    return ActionOperation.from_action(action)


class ActionOperation:
    @staticmethod
    def from_action(action: ActionDict) -> "ActionOperation":
        action_type = action["action"]["type"]
        cls = ACTION_TYPE_MAPPING[action_type]
        return cls.from_action(action)

    def apply(self, step: SubmissionStep, configuration: JSONObject) -> None:
        """
        Implements the side effects of the action operation.
        """
        pass


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

    def apply(self, step: SubmissionStep, configuration: JSONObject) -> None:
        component = get_component(configuration, key=self.component)
        if component is None:
            return
        component[self.property] = self.value


class DisableNextAction(ActionOperation):
    @classmethod
    def from_action(cls, action: ActionDict) -> "DisableNextAction":
        return cls()

    def apply(self, step: SubmissionStep, configuration: JSONObject) -> None:
        step._can_submit = False


@dataclass
class StepNotApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> "StepNotApplicableAction":
        return cls(
            form_step_identifier=action["form_step"],
        )

    def apply(self, step: SubmissionStep, configuration: JSONObject) -> None:
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


ACTION_TYPE_MAPPING = {
    LogicActionTypes.property: PropertyAction,
    LogicActionTypes.disable_next: DisableNextAction,
    LogicActionTypes.step_not_applicable: StepNotApplicableAction,
}
