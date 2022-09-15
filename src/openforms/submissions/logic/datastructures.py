from openforms.typing import DataMapping

from ..datastructures import DataContainer as _DataContainer
from ..models import SubmissionStep


class DataContainer(_DataContainer):
    """
    A data container to manage the data/variables lifecycle during logic evaluation.
    """

    def get_updated_step_data(self, step: SubmissionStep) -> DataMapping:
        relevant_variables = self.state.get_variables_in_submission_step(
            step, include_unsaved=True
        )
        return {
            key: variable.value
            for key, variable in relevant_variables.items()
            if not variable.form_variable
            or variable.value != variable.form_variable.initial_value
        }
