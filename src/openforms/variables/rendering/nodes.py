from dataclasses import dataclass
from typing import Any, Iterator, Union

from openforms.formio.rendering.conf import RENDER_CONFIGURATION
from openforms.formio.rendering.constants import RENDER_CONFIGURATION_CAMEL_TO_SNAKE
from openforms.forms.constants import FormVariableSources
from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.submissions.rendering import RenderModes
from openforms.submissions.rendering.base import Node


@dataclass
class VariablesNode(Node):
    submission: Submission

    @property
    def is_visible(self) -> bool:
        return self.submission.submissionvaluevariable_set.filter(
            form_variable__source=FormVariableSources.user_defined
        ).exists()

    def render(self) -> str:
        return "Variables"

    def get_children(self) -> Iterator["Node"]:
        if not self.is_visible:
            return

        variables = self.submission.submissionvaluevariable_set.filter(
            form_variable__source=FormVariableSources.user_defined
        ).select_related("form_variable")
        for variable in variables:
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
        render_configuration = RENDER_CONFIGURATION[self.mode]
        if render_configuration.key is None:
            return render_configuration.default

        should_render = getattr(
            self.variable.form_variable,
            RENDER_CONFIGURATION_CAMEL_TO_SNAKE[render_configuration.key],
            render_configuration.default,
        )
        return should_render

    @property
    def value(self) -> Any:
        return self.variable.value

    def get_children(self) -> Iterator["Node"]:
        return iter([])

    @property
    def label(self) -> str:
        return self.variable.key

    @property
    def display_value(self) -> Union[str, Any]:
        # in export mode, expose the raw datatype
        if self.mode == RenderModes.export:
            return self.variable.value

        # TODO add a registry of formatters like for Formio ComponentNodes
        return self.variable.value

    def render(self) -> str:
        return f"{self.label}: {self.display_value}"
