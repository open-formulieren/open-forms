"""
Core renderer implementation.

The renderer is the public interface to rendering submissions in particular render
modes. It is aware of the intrinsic tree-like structure of a submission and associated
printable data.
"""
from dataclasses import dataclass
from typing import Iterator

from openforms.forms.models import Form

from ..models import Submission
from .base import Node
from .constants import RenderModes  # noqa
from .nodes import FormNode, SubmissionStepNode


@dataclass
class Renderer:
    """
    A submission renderer.

    Instantiate an object of this class with the desired render mode, and then you
    can use this object in template or python code to emit the desired markup/
    formatting.
    """

    # render context, passed to all underlying nodes
    submission: Submission
    mode: str
    as_html: bool

    @property
    def form(self) -> Form:
        """
        Get the associated :class:`openforms.forms.models.Form` instance.
        """
        return self.submission.form

    @property
    def steps(self):
        """
        Return the submission steps in the correct order.
        """
        steps_qs = self.submission.submissionstep_set.select_related(
            "form_step", "form_step__form_definition"
        ).order_by("form_step__order")
        return steps_qs

    def get_children(self) -> Iterator["SubmissionStepNode"]:
        """
        Produce only the direct child nodes.
        """
        common_kwargs = {"renderer": self}
        for step in self.steps:
            submission_step_node = SubmissionStepNode(step=step, **common_kwargs)
            if not submission_step_node.is_visible:
                continue

            # formio_configuration_node = FormioConfigurationNode(
            #     step=step, **common_kwargs
            # )
            # has_any_children = any(
            #     child.is_visible for child in formio_configuration_node
            # )
            # if not has_any_children:
            #     continue
            yield submission_step_node

    def __iter__(self) -> Iterator["Node"]:
        """
        Yield the nodes to visualize a complete submission.
        """
        yield FormNode(renderer=self)
        for child in self.get_children():
            yield child
            yield from child
