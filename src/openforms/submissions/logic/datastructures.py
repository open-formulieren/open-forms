from dataclasses import dataclass, field
from typing import Any

from openforms.formio.service import FormioData
from openforms.typing import DataMapping

from ..models import SubmissionStep
from ..models.submission_value_variable import SubmissionValueVariablesState


@dataclass
class DataContainer:
    """
    A data container to manage the data/variables lifecycle during logic evaluation.
    """

    state: SubmissionValueVariablesState

    _initial_data: tuple[tuple[str, Any]] = field(init=False, default_factory=tuple)

    def __post_init__(self):
        # ensure the initial data is immutable
        self._initial_data = tuple(self.data.items())  # record for logging purposes

    @property
    def initial_data(self) -> DataMapping:
        return dict(self._initial_data)

    @property
    def data(self) -> DataMapping:
        """
        Collect the total picture of data/variable values.

        The current view on the submission variable value state is augmented with
        the static variables.

        :return: A datamapping (key: variable key, value: variable value) ready for
          (template context) evaluation.
        """
        dynamic_values = {
            key: variable.to_python() for key, variable in self.state.variables.items()
        }
        static_values = self.state.static_data()
        nested_data = FormioData({**dynamic_values, **static_values})
        return nested_data.data

    def update(self, updates: DataMapping) -> None:
        """
        Update the dynamic data state.
        """
        self.state.set_values(updates)

    def get_updated_step_data(self, step: SubmissionStep) -> FormioData:
        relevant_variables = self.state.get_variables_in_submission_step(
            step, include_unsaved=True
        )

        updated_data = FormioData()
        for key, variable in relevant_variables.items():
            if (
                not variable.form_variable
                or variable.value != variable.form_variable.initial_value
            ):
                updated_data[key] = variable.value
        return updated_data
