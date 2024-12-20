import base64

from django.utils.translation import gettext_lazy as _

from zgw_consumers.client import build_client

from openforms.submissions.models import Submission
from openforms.variables.service import get_static_variables

from ...base import BasePlugin  # openforms.registrations.base
from ...registry import register  # openforms.registrations.registry
from ...utils import execute_unless_result_exists
from .config import JSONOptions, JSONOptionsSerializer


@register("json")
class JSONRegistration(BasePlugin):
    verbose_name = _("JSON registration")
    configuration_options = JSONOptionsSerializer

    def register_submission(self, submission: Submission, options: JSONOptions) -> None:
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

        # Create static variables dict
        static_variables = get_static_variables(submission=submission)
        static_variables_dict = {
            variable.key: variable.initial_value for variable in static_variables
        }

        # TODO-4908: what should the behaviour be when a form variable is not in the data or static variables?
        #  Raising an error probably a good idea, the form variable is currently just set to None in the
        #  resulting values dict
        # Update values dict with relevant form data
        values.update({
            form_variable: submission.data.get(
                form_variable, static_variables_dict.get(form_variable)
            )
            for form_variable in options["form_variables"]
        })

        print(values)

        # Send to the service
        json = {"values": values}
        service = options["service"]
        with build_client(service) as client:
            response = client.post(
                options.get("relative_api_endpoint", ""),
                json=json,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            print(response.json())

        # TODO-4908: added return for testing purposes
        return json

    def check_config(self):
        # TODO-4098: check if it's possible to connect to the service
        #  (using the 'connection check endpoint' of the service)
        # TODO-4098: check anything else?
        pass
