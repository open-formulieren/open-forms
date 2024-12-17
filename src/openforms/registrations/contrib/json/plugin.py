from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission
from ...base import BasePlugin, OptionsT  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import JSONOptionsSerializer


@register("json")
class JSONPlugin(BasePlugin):
    verbose_name = _("JSON registration")
    configuration_options = JSONOptionsSerializer

    def register_submission(self, submission: Submission, options: OptionsT) -> None:
        print(options)

    def check_config(self):
        pass
