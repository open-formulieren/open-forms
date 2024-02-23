from typing import NoReturn

from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...exceptions import RegistrationFailed
from ...registry import register
from .config import DemoOptionsSerializer


@register("demo")
class DemoRegistration(BasePlugin):
    verbose_name = _("Demo - print to console")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: dict) -> None:
        print(submission)
        if options.get("extra_line"):
            print(options["extra_line"])

    def update_payment_status(self, submission: "Submission", options: dict):
        print(submission)

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass


@register("failing-demo")
class DemoFailRegistration(BasePlugin):
    verbose_name = _("Demo - fail registration")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: dict) -> NoReturn:
        raise RegistrationFailed("Demo failing registration")

    def update_payment_status(self, submission: "Submission", options: dict):
        pass

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass


@register("exception-demo")
class DemoExceptionRegistration(BasePlugin):
    verbose_name = _("Demo - exception during registration")
    configuration_options = DemoOptionsSerializer
    is_demo_plugin = True

    def register_submission(self, submission: Submission, options: dict) -> NoReturn:
        raise Exception("Demo exception registration")

    def update_payment_status(self, submission: "Submission", options: dict):
        pass

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
