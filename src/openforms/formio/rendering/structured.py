from typing import TYPE_CHECKING

from openforms.formio.service import FormioData
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.rendering.nodes import SubmissionStepNode
from openforms.typing import JSONObject

from .default import ColumnsNode, EditGridGroupNode, EditGridNode, FieldSetNode
from .nodes import ComponentNode

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def render_json(submission: "Submission") -> JSONObject:
    """Render submission as JSON with nesting

    The data is nested within each submission step (using the form definition slug as key).
    The data is nested for fieldset components and for column components.

    This is different from how Formio treats fieldsets/columns in the submission data: their children are not
    nested. We treat them more like Formio treats the 'container' component (currently not supported in Open Forms).
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

            data[node_path] = value

    return data.data
