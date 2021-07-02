from typing import Optional

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...exceptions import RegistrationFailed
from ...registry import register
from .config import DemoOptionsSerializer


@register("demo")
class DemoRegistration(BasePlugin):
    verbose_name = _("Demo - print to console")
    configuration_options = DemoOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        print(submission)
        print(options["extra_line"])


@register("failing-demo")
class DemoFailRegistration(BasePlugin):
    verbose_name = _("Demo - fail registration")
    configuration_options = DemoOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Optional[dict]:
        raise RegistrationFailed("Demo failing registration")
