from typing import Optional

from django.template import Context, Template

from rest_framework.request import Request

from openforms.contrib.camunda.dmn import evaluate_dmn
from openforms.formio.typing import Component
from openforms.forms.custom_field_types import register
from openforms.submissions.models import Submission, SubmissionStep


@register("camunda:dmn")
def evaluate_camunda_dmn(
    component: Component,
    request: Request,
    submission: Submission,
    step: Optional[SubmissionStep] = None,
) -> Component:
    # TODO: possibly cache (functools.lrucache?) based on component ID & input variables
    # to avoid repeated calls to the Camunda API?W

    # TODO: we might want to parse the DMN XML to figure out which input data keys are needed,
    # or use an explicit mapping of component -> input to avoid sending potentially
    # sensitive data into the Camunda API.
    # TODO: right now, the component key must match the inputData key in the DMN model,
    # it should be possible to apply a mapping for this.
    input_values = submission.data
    result = evaluate_dmn(component["decisionTableKey"], input_values=input_values)

    # persist the evaluation result as a value on the submission step
    if step is not None:
        if step.data is None:
            step.data = {}
        if (key := component["key"]) not in step.data or step.data[key] != result:
            step.data[key] = result
            step.save(update_fields=["data"])

    context_data = {
        "result": result,
        "submission_data": submission.data,
    }
    output = Template(component["resultDisplayTemplate"]).render(Context(context_data))
    component["resultDisplay"] = output

    # set the default value to communicate the evaluation result, the SDK can/should pick
    # this up.
    component["defaultValue"] = result

    return component
