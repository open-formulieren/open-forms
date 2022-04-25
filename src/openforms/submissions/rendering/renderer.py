"""
High-level submission renderer capable of outputting to different modes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Optional

from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

from openforms.forms.models import Form, FormStep

from ..models import Submission, SubmissionStep

NODE_TYPES = {}


class RenderModes(DjangoChoices):
    cli = ChoiceItem("cli", _("CLI"))
    pdf = ChoiceItem("pdf", _("PDF"))
    confirmation_email = ChoiceItem("confirmation_email", _("Confirmation email"))
    export = ChoiceItem("export", _("Submission export"))
    # registration_email = ChoiceItem('registration_email', _("Registration email"))


@dataclass
class Renderer:
    # render context
    submission: Submission
    mode: str
    as_html: bool
    limit_value_keys: Optional[List[str]] = None

    @property
    def form(self) -> Form:
        return self.submission.form

    def render(self) -> Iterator["Node"]:
        common_kwargs = {"renderer": self}

        # emit a FormNode so the form itself is accessible
        yield FormNode(**common_kwargs)

        # now emit the form steps, which in turn emit their children in a depth-first
        # pattern.
        steps_qs = self.submission.submissionstep_set.select_related(
            "form_step", "form_step__form_definition"
        ).order_by("form_step__order")
        for step in steps_qs:
            yield SubmissionStepNode(step=step, **common_kwargs)
            yield FormStepNode(step=step.form_step, **common_kwargs)


@dataclass
class Node(ABC):
    """
    Abstract node base class.

    All specific render node types must inherit from this class.
    """

    renderer: Renderer

    def __init_subclass__(cls, **kwargs):
        # register subclasses as node types so we can pass this to django template
        # rendering context
        NODE_TYPES[cls.__name__] = cls

    @property
    def type(self) -> str:
        """
        Name of the node type
        """
        return type(self).__name__

    @property
    def mode(self) -> str:
        return self.renderer.mode

    @property
    def as_html(self) -> bool:
        return self.renderer.as_html

    @abstractmethod
    def render(self) -> str:
        """
        Output the result of rendering the particular type of node given a context.
        """
        ...


@dataclass
class FormNode(Node):
    def render(self) -> str:
        form = self.renderer.form
        return form.name


@dataclass
class SubmissionStepNode(Node):
    step: SubmissionStep

    def render(self) -> str:
        return ""


@dataclass
class FormStepNode(Node):
    step: FormStep

    def render(self) -> str:
        form_definition = self.step.form_definition
        return form_definition.name
