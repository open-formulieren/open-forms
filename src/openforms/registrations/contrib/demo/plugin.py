from typing import NoReturn

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference, RegistrationFailed
from ...registry import register
from .config import DemoOptionsSerializer


@register("demo")
class DemoRegistration(BasePlugin):
    verbose_name = _("Demo - print to console")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: dict) -> None:
        print(submission)
        print(options["extra_line"])

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Demo plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission"):
        print(submission)

    def test_config(self) -> None:
        print("test plugin")


@register("failing-demo")
class DemoFailRegistration(BasePlugin):
    verbose_name = _("Demo - fail registration")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: dict) -> NoReturn:
        raise RegistrationFailed("Demo failing registration")

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Demo plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission"):
        pass

    def test_config(self) -> None:
        print("test plugin")
