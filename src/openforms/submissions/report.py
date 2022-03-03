"""
Utility classes for the submission report rendering.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator

from openforms.formio.formatters.service import filter_printable, format_value
from openforms.formio.typing import Component
from openforms.forms.models import Form

if TYPE_CHECKING:
    from .models import Submission, SubmissionStep


@dataclass
class DataItem:
    component: Component
    value: Any

    @property
    def label(self) -> str:
        return self.component.get("label") or self.component.get("key", "")

    @property
    def layout_modifier(self) -> str:
        if self.component.get("type") == "fieldset":
            return "fieldset"
        return ""

    @property
    def display_value(self) -> str:
        return format_value(self.component, self.value)


@dataclass
class ReportStep:
    """
    A wrapper around a submission step outputting the step-specific data.
    """

    step: "SubmissionStep"

    @property
    def title(self) -> str:
        return self.step.form_step.form_definition.name

    def __iter__(self) -> Iterator[DataItem]:
        """
        Return the individual 'key-value' items for the data in the step.
        """
        iter_components = self.step.form_step.iter_components(recursive=True)
        for component in filter_printable(iter_components):
            key = component["key"]
            value = self.step.data.get(key)
            yield DataItem(component=component, value=value)


@dataclass
class Report:
    submission: "Submission"

    @property
    def form(self) -> Form:
        return self.submission.form

    @property
    def show_payment_info(self) -> bool:
        return self.submission.payment_required and self.submission.price

    @property
    def steps(self) -> Iterator[ReportStep]:
        for step in self.submission.submissionstep_set.order_by("form_step__order"):
            yield ReportStep(step=step)
