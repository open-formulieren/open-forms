from dataclasses import dataclass
from typing import Any, Iterator, Union

from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.submissions.rendering import RenderModes
from openforms.submissions.rendering.base import Node
from openforms.variables.constants import FormVariableSources


@dataclass
class VariablesNode(Node):
    """
    Render node for the user defined variables related to a form.

    This node is only 'visible' for certain render modes (cli and registration), but it is not rendered if there are
    user defined variables related to the form.
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
            self._variables = self.submission.submissionvaluevariable_set.filter(
                form_variable__source=FormVariableSources.user_defined
            ).select_related("form_variable")
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
    def display_value(self) -> Union[str, Any]:
        # If we are going to render in different modes, we will need to add a registry of formatters
        # like for Formio ComponentNodes
        return self.variable.value

    def render(self) -> str:
        return f"{self.label}: {self.display_value}"
