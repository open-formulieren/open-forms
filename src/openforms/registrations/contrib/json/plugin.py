import base64

from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.submissions.models import Submission
from openforms.variables.service import get_static_variables

from ...base import BasePlugin, OptionsT  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from ...utils import execute_unless_result_exists
from .config import JSONOptionsSerializer


@register("json")
class JSONRegistration(BasePlugin):
    verbose_name = _("JSON registration")
    configuration_options = JSONOptionsSerializer

    def register_submission(self, submission: Submission, options: OptionsT) -> None:
        # TODO-4908: the email plugin works with a EmailConfig singleton model. Is that useful here?
        # TODO-4908: add typing for options dict

        # TODO-4908: any other form field types that need 'special attention'?

        values = {}
        # Encode (base64) and add attachments to values dict if their form keys were specified in the
        # form variables list
        for attachment in submission.attachments:
            if not attachment.form_key in options["form_variables"]:
                continue
            options["form_variables"].remove(attachment.form_key)
            with attachment.content.open("rb") as f:
                f.seek(0)
                values[attachment.form_key] = base64.b64encode(f.read()).decode()

        # TODO-4908: what should the behaviour be when a form
        #  variable is not in the data or static variables?
        # Create static variables dict
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

        # Send to the service
        json = {"values": values}
        service = options["service"]
        submission.registration_result = result = {}
        with build_client(service) as client:
            result["api_response"] = res = client.post(
                options.get("relative_api_endpoint", ""),
                json=json,
                headers={"Content-Type": "application/json"},
            )
            res.raise_for_status()

        return result

    def check_config(self) -> None:
        # Config checks are not really relevant for this plugin right now
        pass
