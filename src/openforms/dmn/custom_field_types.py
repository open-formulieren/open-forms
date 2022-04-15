from django.template import Context, Template

import requests
from glom import glom
from rest_framework.request import Request

from openforms.formio.typing import Component
from openforms.forms.custom_field_types import register as fields_register
from openforms.submissions.models import Submission

from .models import DMNEvaluationResult
from .registry import register


@fields_register("dmn")
def evaluate_dmn(
    component: Component,
    request: Request,
    submission: Submission,
) -> Component:
    # TODO: possibly cache (functools.lrucache?) based on component ID & input variables
    # to avoid repeated calls to the Camunda API?W

    # TODO: we might want to parse the DMN XML to figure out which input data keys are needed,
    # or use an explicit mapping of component -> input to avoid sending potentially
    # sensitive data into the Camunda API. Note this also ties in with the future variables
    # implementation.

    # TODO: right now, the component key must match the inputData key in the DMN model,
    # it should be possible to apply a mapping for this.
    input_values = submission.data
    if not input_values:
        return component

    # add the default values, these don't seem to be submitted by Formio
    for _component in submission.form.iter_components():
        if not (key := _component.get("key")):
            continue
        if _component.get("type") != "radio":
            continue

        if input_values.get(key) == "" and _component.get("defaultValue") != "":
            input_values[key] = _component["defaultValue"]

    configuration = component["dmn"]

    plugin = register[configuration["engine"]["id"]]
    definition_id = configuration["decisionDefinition"]["id"]
    definition_version = glom(configuration, "decisionDefinitionVersion.id", default="")
    result_template = configuration["resultDisplayTemplate"]

    try:
        result = plugin.evaluate(
            definition_id, version=definition_version, input_values=input_values
        )
    except requests.HTTPError as exc:
        result = {}
        output = exc.response.json()["message"]
    else:
        context_data = {
            "result": result,
            "submission_data": submission.data,
        }
        output = Template(result_template).render(Context(context_data))

    # save so we can use it in prefill
    eval_result, _ = DMNEvaluationResult.objects.update_or_create(
        submission=submission, component=component["key"], defaults={"result": result}
    )

    component["dmn"]["resultDisplay"] = output

    # set the default value to communicate the evaluation result, the SDK can/should pick
    # this up.
    component["defaultValue"] = result

    return component
