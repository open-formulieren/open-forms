from rest_framework.request import Request

from openforms.formio.typing import Component
from openforms.forms.custom_field_types import register
from openforms.submissions.models import Submission


@register("camunda:dmn")
def evaluate_camunda_dmn(
    component: Component,
    request: Request,
    submission: Submission,
) -> Component:
    raise NotImplementedError("TODO")
    return component
