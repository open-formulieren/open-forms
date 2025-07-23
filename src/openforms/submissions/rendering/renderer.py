"""
Core renderer implementation.

The renderer is the public interface to rendering submissions in particular render
modes. It is aware of the intrinsic tree-like structure of a submission and associated
printable data.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from openforms.forms.models import Form
from openforms.variables.rendering.nodes import VariablesNode

from ..form_logic import evaluate_form_logic
from ..models import Submission
from .base import Node
from .constants import RenderModes
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
    mode: RenderModes
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
        return self.submission.steps

    @property
    def has_children(self) -> bool:
        generator = self.get_children()
        try:
            next(generator)
        except StopIteration:
            return False
        else:
            return True

    def get_children(self) -> Iterator[SubmissionStepNode | VariablesNode]:
        """
        Produce only the direct child nodes.
        """
        for step in self.steps:
            new_configuration = evaluate_form_logic(
                submission=self.submission, step=step
            )
            # update the configuration for introspection - note that we are mutating
            # an instance here without persisting it to the backend on purpose!
            # this replicates the run-time behaviour while filling out the form
            step.form_step.form_definition.configuration = new_configuration
            submission_step_node = SubmissionStepNode(renderer=self, step=step)
            if not submission_step_node.is_visible:
                continue

            has_visible_children = any(
                child for child in submission_step_node if child.is_visible
            )
            if not has_visible_children:
                continue

            yield submission_step_node

        variables_node = VariablesNode(renderer=self, submission=self.submission)
        has_visible_variable_children = any(
            child for child in variables_node if child.is_visible
        )
        if has_visible_variable_children:
            yield variables_node

    def __iter__(self) -> Iterator[Node]:
        """
        Yield the nodes to visualize a complete submission.
        """
        yield FormNode(renderer=self)
        for child in self.get_children():
            yield child
            yield from child
