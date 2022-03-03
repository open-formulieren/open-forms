"""
Utility classes for the submission report rendering.
"""
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator

from django.utils.safestring import SafeString

from openforms.formio.formatters.service import format_value
from openforms.formio.typing import Component
from openforms.forms.models import Form

if TYPE_CHECKING:
    from .models import Submission, SubmissionStep

logger = logging.getLogger(__name__)


@dataclass
class DataItem:
    component: Component
    value: Any

    @property
    def label(self) -> str:
        return self.component.get("label") or self.component.get("key", "")

    @property
    def layout_modifier(self) -> str:
        type = self.component.get("type")
        if type == "fieldset":
            return "fieldset"
        elif type == "columns":
            return "columns"
        return "root" if self.component.get("_is_root", False) else ""

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
        # TODO: find a better mechanism to extract the "root" information instead of
        # polluting the Formio component schema, preferably without breaking a lot of tests
        iter_components = self.step.form_step.iter_components(
            recursive=True, _mark_root=True
        )
        for component in iter_components:
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

    @property
    def co_signer(self) -> str:
        if not self.submission.co_sign_data:
            return ""

        if not (co_signer := self.submission.co_sign_data.get("representation", "")):
            logger.warning(
                "Incomplete co-sign data for submission %s", self.submission.uuid
            )

        return co_signer

    @property
    def confirmation_page_content(self) -> SafeString:
        # the content is already escaped by Django's rendering engine and mark_safe
        # has been applied by ``Template.render``
        content = self.submission.render_confirmation_page()
        return content
