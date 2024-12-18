from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission
from openforms.variables.service import get_static_variables

from ...base import BasePlugin, OptionsT  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from .config import JSONOptionsSerializer


@register("json")
class JSONRegistration(BasePlugin):
    verbose_name = _("JSON registration")
    configuration_options = JSONOptionsSerializer

    def register_submission(self, submission: Submission, options: OptionsT) -> None:
        static_variables = get_static_variables(submission=submission)
        static_variables_dict = {
            variable.key: variable.initial_value for variable in static_variables
        }

        # Update values dict with relevant form data
        all_variables = {**submission.data, **static_variables_dict}
        values.update(
            {
                form_variable: all_variables[form_variable]
                for form_variable in options["form_variables"]
            }
        )

        print(values)

        # TODO-4908: send `values` to some service
        data_to_be_sent = {"values": values}

    def check_config(self):
        pass
