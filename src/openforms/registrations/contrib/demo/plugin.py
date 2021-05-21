from typing import NoReturn

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission

from ...exceptions import RegistrationFailed
from ...registry import register
from .config import DemoOptionsSerializer


@register(
    unique_identifier="demo",
    name=_("Demo - print to console"),
    configuration_options=DemoOptionsSerializer,
)
def handle_submission(submission: Submission, options: dict) -> None:
    print(submission)
    print(options["extra_line"])


@register(
    unique_identifier="failing-demo",
    name="Demo - fail registration",
    configuration_options=DemoOptionsSerializer,
)
def failing_callback(submission: Submission, options: dict) -> NoReturn:
    raise RegistrationFailed("Demo failing registration")
