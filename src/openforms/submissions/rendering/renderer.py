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
from openforms.forms.models import Form, FormStep

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

    @property
    def form(self) -> Form:
        return self.submission.form

    def render(self) -> Iterator["Node"]:
        common_kwargs = {"renderer": self}
        dummy_request = get_request()

        # emit a FormNode so the form itself is accessible
        yield FormNode(**common_kwargs)

        # now emit the form steps, which in turn emit their children in a depth-first
        # pattern.
        steps_qs = self.submission.submissionstep_set.select_related(
            "form_step", "form_step__form_definition"
        ).order_by("form_step__order")
        for step in steps_qs:
            new_configuration = evaluate_form_logic(
                submission=self.submission,
                step=step,
                data=self.submission.data,
                dirty=False,
                request=dummy_request,
            )
            # update the configuration for introspection - note that we are mutating
            # an instance here without persisting it to the backend on purpose!
            # this replicates the run-time behaviour while filling out the form
            step.form_step.form_definition.configuration = new_configuration

            submission_step_node = SubmissionStepNode(step=step, **common_kwargs)
            form_step_node = FormStepNode(step=step.form_step, **common_kwargs)
            formio_configuration_node = FormioConfigurationNode(
                step=step, **common_kwargs
            )
            has_any_children = any(
                child.is_visible for child in formio_configuration_node
            )
            if not has_any_children:
                continue

            yield submission_step_node
            yield form_step_node
            # at this point, hand over to the formio specific implementation details
            yield from formio_configuration_node


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
