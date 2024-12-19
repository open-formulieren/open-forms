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

        values = {}
        if submission.attachments.exists():
            for attachment in submission.attachments:
                if not attachment.form_key in options["form_variables"]:
                    continue
                options["form_variables"].remove(attachment.form_key)
                with attachment.content.open("rb") as f:
                    values[attachment.form_key] = f.read()

        # TODO-4908: what should the behaviour be when a form
        #  variable is not in the data or static variables?
        values.update({
            form_variable: submission.data.get(
                form_variable, static_variables_dict.get(form_variable)
            )
            for form_variable in options["form_variables"]
        })

        print(values)

        # TODO-4908: send `values` to the service
        # TODO-4908: added return for testing purposes
        return {"values": values}

    def check_config(self):
        pass
