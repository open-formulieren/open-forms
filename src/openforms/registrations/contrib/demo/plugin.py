from openforms.submissions.models import Submission

from ...registry import register
from .config import DemoOptionsSerializer


@register(
    unique_identifier="demo",
    name="Demo - print to console",
    configuration_options=DemoOptionsSerializer,
)
def handle_submission(submission: Submission, options: dict) -> None:
    print(submission)
    print(options["extra_line"])
