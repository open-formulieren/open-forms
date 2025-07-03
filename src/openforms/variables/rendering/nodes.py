from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.submissions.rendering import RenderModes
from openforms.submissions.rendering.base import Node
from openforms.variables.constants import FormVariableSources


@dataclass
class VariablesNode(Node):
    """
    Render node for the user defined variables related to a form.

    This node is only 'visible' for certain render modes (cli and registration), but it
    is not rendered if there are user defined variables related to the form.
    """

    submission: Submission

    _variables = None

    @property
    def is_visible(self) -> bool:
        if self.mode not in [RenderModes.cli, RenderModes.registration]:
            return False
        return len(self.variables) > 0

    @property
    def variables(self):
        if not self._variables:
            variables_state = self.submission.load_submission_value_variables_state()
            relevant_vars = [
                variable
                for variable in variables_state.variables.values()
                if variable.pk
                # if there is no form variable, this may be because the form step and
                # form definition were deleted, which makes it by definition not a user-defined variable
                and variable.form_variable
                and variable.form_variable.source == FormVariableSources.user_defined
            ]
            self._variables = sorted(relevant_vars, key=lambda variable: variable.pk)
        return self._variables

    def render(self) -> str:
        if not self.is_visible:
            return ""
        return _("Variables")

    def get_children(self) -> Iterator["Node"]:
        for variable in self.variables:
            node = SubmissionValueVariableNode(
                renderer=self.renderer, variable=variable
            )
            if node.is_visible:
                yield node


@dataclass
class SubmissionValueVariableNode(Node):
    variable: SubmissionValueVariable
    depth: int = 0
    is_layout: bool = False

    @property
    def is_visible(self) -> bool:
        if self.mode in [RenderModes.export, RenderModes.registration, RenderModes.cli]:
            return True
        return False

    @property
    def value(self) -> Any:
        return self.variable.value

    def get_children(self) -> Iterator["Node"]:
        return iter([])

    @property
    def label(self) -> str:
        if self.mode == RenderModes.export:
            return self.variable.key
        return self.variable.form_variable.name

    @property
    def display_value(self) -> str | Any:
        # If we are going to render in different modes, we will need to add a registry of formatters
        # like for Formio ComponentNodes
        return self.variable.value

    def render(self) -> str:
        return f"{self.label}: {self.display_value}"
