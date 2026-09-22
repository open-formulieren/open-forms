from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from openforms.formio.service import FormioData
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.rendering.nodes import SubmissionStepNode
from openforms.typing import VariableValue

from .default import ColumnsNode, EditGridGroupNode, EditGridNode, FieldSetNode
from .nodes import ComponentNode

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def reshape_submission_data_for_json_summary(
    submission: Submission,
    *,
    use_legacy_mode_for_datelike: bool = False,
) -> dict[str, VariableValue]:
    """Reshape the submission data for rendering a JSON summary.

    The data is nested within each submission step (using the form definition slug as
    key). The data is nested for fieldset components and for column components.

    This is different from how Formio treats fieldsets/columns in the submission data:
    their children are not nested. We treat them more like Formio treats the 'container'
    component (currently not supported in Open Forms).
    """
    renderer = Renderer(
        submission=submission, mode=RenderModes.registration, as_html=False
    )

    data = FormioData()
    current_step_slug = None
    for node in renderer:
        if isinstance(node, SubmissionStepNode):
            current_step_slug = node.step.form_step.slug
            data[current_step_slug] = {}
            continue

        if isinstance(node, EditGridGroupNode):
            node_path = f"{current_step_slug}.{node.json_renderer_path}"
            editgrid_array = data[node_path]
            editgrid_array.append({})
            continue

        if isinstance(node, ComponentNode):
            node_path = (
                f"{current_step_slug}.{node.json_renderer_path}.{node.key}"
                if node.json_renderer_path
                else f"{current_step_slug}.{node.key}"
            )

            value = {} if isinstance(node, FieldSetNode | ColumnsNode) else node.value
            if isinstance(node, EditGridNode):
                value = []

            # backwards compatibility shim...
            if (
                node.component["type"] in ("date", "datetime", "time")
                and use_legacy_mode_for_datelike
            ):
                warnings.warn(
                    "Converting empty date/datetime/time values to empty string is "
                    "deprecated and scheduled for removal in Open Forms 5.0",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if value is None:
                    value = ""
                elif isinstance(value, list):  # multiple
                    value = [item or "" for item in value]

            data[node_path] = value

    return data.data
