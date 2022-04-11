from openforms.submissions.models import Submission

from .constants import OutputMode
from .elements import create_elements
from .registry import register
from .render import RenderContext, render_elements
from .wrap import get_submission_tree

__all__ = ["render", "OutputMode"]


def render(
    submission: Submission, *, mode: OutputMode, as_html: bool, limit_value_keys=None
) -> str:
    context = RenderContext(
        mode=mode, as_html=as_html, limit_value_keys=limit_value_keys
    )
    root = get_submission_tree(submission, register)

    elements = create_elements(root.children, context)
    return render_elements(elements, context)
