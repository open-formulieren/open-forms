from typing import NoReturn

from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...exceptions import RegistrationFailed
from ...registry import register
from .config import DemoOptions, DemoOptionsSerializer


@register("demo")
class DemoRegistration(BasePlugin[DemoOptions]):
    verbose_name = _("Demo - print to console")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: DemoOptions) -> None:
        print(submission)
        if extra_line := options.get("extra_line"):
            print(extra_line)

    def update_payment_status(self, submission: "Submission", options: DemoOptions):
        print(submission)

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass


@register("failing-demo")
class DemoFailRegistration(BasePlugin[DemoOptions]):
    verbose_name = _("Demo - fail registration")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(
        self, submission: Submission, options: DemoOptions
    ) -> NoReturn:
        raise RegistrationFailed("Demo failing registration")

    def update_payment_status(self, submission: "Submission", options: DemoOptions):
        pass

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass


@register("exception-demo")
class DemoExceptionRegistration(BasePlugin[DemoOptions]):
    verbose_name = _("Demo - exception during registration")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(
        self, submission: Submission, options: DemoOptions
    ) -> NoReturn:
        raise Exception("Demo exception registration")

    def update_payment_status(self, submission: "Submission", options: DemoOptions):
        pass

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
