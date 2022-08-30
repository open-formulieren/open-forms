from openforms.celery import app

from ...variables.constants import FormVariableSources
from ..form_logic import evaluate_form_logic
from ..models import Submission, SubmissionValueVariable
from ..rendering.utils import get_request


@app.task
def persist_user_defined_variables(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    data = submission.data

    last_form_step = submission.submissionstep_set.order_by("form_step__order").last()
    if not last_form_step:
        return

    evaluate_form_logic(
        submission, last_form_step, data, dirty=False, request=get_request()
    )

    state = submission.load_submission_value_variables_state()
    variables = state.variables

    user_defined_vars_data = {
        variable.key: variable.value
        for variable_key, variable in variables.items()
        if variable.form_variable.source == FormVariableSources.user_defined
    }

    if user_defined_vars_data:
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            user_defined_vars_data, submission
        )
