from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Optional, TypedDict

from glom import assign
from json_logic import jsonLogic

from openforms.formio.service import FormioConfigurationWrapper
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import FormLogic, FormVariable
from openforms.typing import DataMapping, JSONObject, JSONValue
from openforms.utils.json_logic import ComponentMeta
from openforms.variables.models import ServiceFetchConfiguration

from ..models import Submission, SubmissionStep
from ..models.submission_step import DirtyData
from .log_utils import log_errors
from .service_fetching import perform_service_fetch


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
    action_type = action["action"]["type"]
    cls = ACTION_TYPE_MAPPING[action_type]
    return cls.from_action(action)


class ActionOperation:
    rule: FormLogic

    @classmethod
    def from_action(cls, action: ActionDict) -> "ActionOperation":
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
        context: DataMapping,
        log: Callable[[JSONValue], None],
        submission: Submission,
    ) -> DataMapping | None:
        """
        Return a mapping [name/path -> new_value] with changes that are to be
        applied to the context.
        """
        pass

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
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
        assign(component, self.property, self.value, missing=dict)

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
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
            "type_display": LogicActionTypes.get_label(LogicActionTypes.property),
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
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
    ) -> JSONObject:
        return {
            "type_display": LogicActionTypes.get_label(LogicActionTypes.disable_next),
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
        submission_step_to_modify.is_applicable = False

        # This clears data in the database to make sure that saved steps which later become
        # not-applicable don't have old data
        submission_step_to_modify.data = {}
        if submission_step_to_modify == step:
            step.is_applicable = False
            step.data = DirtyData({})

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
    ) -> JSONObject:
        return {
            "type_display": LogicActionTypes.get_label(
                LogicActionTypes.step_not_applicable
            ),
            "step_name": self.form_step_identifier,
        }


@dataclass
class StepApplicableAction(ActionOperation):
    form_step_identifier: str

    @classmethod
    def from_action(cls, action: ActionDict) -> "StepApplicableAction":
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

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
    ) -> JSONObject:
        return {
            "type_display": LogicActionTypes.get_label(
                LogicActionTypes.step_applicable
            ),
            "step_name": self.form_step_identifier,
        }


@dataclass
class VariableAction(ActionOperation):
    variable: str
    value: JSONObject

    @classmethod
    def from_action(cls, action: ActionDict) -> "VariableAction":
        return cls(variable=action["variable"], value=action["action"]["value"])

    def eval(
        self,
        context: DataMapping,
        log: Callable[[JSONValue], None],
        submission: Submission,
    ) -> DataMapping:
        with log_errors(self.value, self.rule):
            log({"value": (value := jsonLogic(self.value, context))})
            return {self.variable: value}

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
    ) -> JSONObject:
        return {
            "key": self.variable,
            "type_display": LogicActionTypes.get_label(LogicActionTypes.variable),
            "value": log_data.get("value", ""),  # error caught by log_errors in `eval`
        }


@dataclass
class ServiceFetchAction(ActionOperation):
    variable: str
    fetch_config: int

    @classmethod
    def from_action(cls, action: ActionDict) -> "ServiceFetchAction":
        return cls(variable=action["variable"], fetch_config=action["action"]["value"])

    def eval(
        self,
        context: DataMapping,
        log: Callable[[JSONValue], None],
        submission: Submission,
    ) -> DataMapping:
        # FIXME
        # https://github.com/open-formulieren/open-forms/issues/3052
        if self.fetch_config:  # the old way
            var = FormVariable(
                key=self.variable,
                service_fetch_configuration=ServiceFetchConfiguration.objects.get(
                    pk=self.fetch_config
                ),
            )
        else:  # the current way
            var = self.rule.form.formvariable_set.get(key=self.variable)
        with log_errors({}, self.rule):  # TODO proper error handling
            result = perform_service_fetch(var, context, str(submission.uuid))
            log(asdict(result))
            return {var.key: result.value}

    def get_action_log_data(
        self,
        component_map: dict[str, ComponentMeta],
        all_variables: dict[str, FormVariable],
        initial_data: dict,
        log_data: dict[str, JSONValue],
    ) -> JSONObject:
        return {
            "key": self.variable,
            "type_display": LogicActionTypes.get_label(
                LogicActionTypes.fetch_from_service
            ),
            "value": repr(log_data),
        }


@dataclass
class SetRegistrationBackendAction(ActionOperation):
    registration_backend_key: str

    @classmethod
    def from_action(cls, action: ActionDict) -> "SetRegistrationBackendAction":
        return cls(registration_backend_key=action["action"]["value"])

    def apply(
        self, step: SubmissionStep, configuration: FormioConfigurationWrapper
    ) -> None:
        step.submission.finalised_registration_backend_key = (
            self.registration_backend_key
        )

    def get_action_log_data(self, *args, **kwargs) -> JSONObject:
        return {
            "type_display": LogicActionTypes.get_label(
                LogicActionTypes.set_registration_backend
            ),
            "registration_backend_key": self.registration_backend_key,
        }


ACTION_TYPE_MAPPING: Mapping[LogicActionTypes, type[ActionOperation]] = {
    LogicActionTypes.property: PropertyAction,
    LogicActionTypes.disable_next: DisableNextAction,
    LogicActionTypes.step_not_applicable: StepNotApplicableAction,
    LogicActionTypes.step_applicable: StepApplicableAction,
    LogicActionTypes.variable: VariableAction,
    LogicActionTypes.fetch_from_service: ServiceFetchAction,
    LogicActionTypes.set_registration_backend: SetRegistrationBackendAction,
}
