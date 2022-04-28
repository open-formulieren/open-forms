"""
High-level submission renderer capable of outputting to different modes.
"""
from dataclasses import dataclass
from typing import Iterator, List, Optional
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse

from openforms.formio.rendering import FormioConfigurationNode
from openforms.forms.models import Form

from ..form_logic import evaluate_form_logic
from ..models import Submission, SubmissionStep
from .base import Node
from .constants import RenderModes  # noqa


def get_request() -> HttpRequest:
    base = urlsplit(settings.BASE_URL)
    request = RequestFactory().get(
        reverse("core:form-list"),
        HTTP_HOST=base.netloc,
        **{"wsgi.url_scheme": base.scheme},
    )
    return request


@dataclass
class Renderer:
    # render context
    submission: Submission
    mode: str
    as_html: bool
    limit_value_keys: Optional[List[str]] = None

    def __post_init__(self):
        self.dummy_request = get_request()

    @property
    def form(self) -> Form:
        return self.submission.form

    @property
    def steps(self):
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
            new_configuration = evaluate_form_logic(
                submission=self.submission,
                step=step,
                data=self.submission.data,
                dirty=False,
                request=self.dummy_request,
            )
            # update the configuration for introspection - note that we are mutating
            # an instance here without persisting it to the backend on purpose!
            # this replicates the run-time behaviour while filling out the form
            step.form_step.form_definition.configuration = new_configuration
            submission_step_node = SubmissionStepNode(step=step, **common_kwargs)
            if not submission_step_node.is_visible:
                continue

            formio_configuration_node = FormioConfigurationNode(
                step=step, **common_kwargs
            )
            has_any_children = any(
                child.is_visible for child in formio_configuration_node
            )
            if not has_any_children:
                continue
            yield submission_step_node

    def render(self) -> Iterator["Node"]:
        common_kwargs = {"renderer": self}

        # emit a FormNode so the form itself is accessible
        yield FormNode(**common_kwargs)

        # now emit the form steps, which in turn emit their children in a depth-first
        # pattern.
        for submission_step_node in self.get_children():
            yield submission_step_node
            yield from submission_step_node.get_children()


@dataclass
class FormNode(Node):
    def render(self) -> str:
        form = self.renderer.form
        return form.name


@dataclass
class SubmissionStepNode(Node):
    step: SubmissionStep

    @property
    def is_visible(self) -> bool:
        # determine if the step as a whole is relevant or not. The stap may be not
        # applicable because of form logic.
        logic_evaluated = getattr(self.step, "_form_logic_evaluated", False)
        assert (
            logic_evaluated
        ), "You should ensure that the form logic is evaluated before rendering steps!"
        return self.step.is_applicable

    def render(self) -> str:
        form_definition = self.step.form_step.form_definition
        return form_definition.name

    def get_children(self) -> Iterator["Node"]:
        if not self.is_visible:
            return

        # at this point, hand over to the formio specific implementation details
        formio_configuration_node = FormioConfigurationNode(
            step=self.step, renderer=self.renderer
        )
        yield from formio_configuration_node
