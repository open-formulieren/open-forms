from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.clients.utils import get_today
from openforms.registrations.constants import REGISTRATION_ATTRIBUTE
from openforms.submissions.mapping import apply_data_mapping
from openforms.submissions.models import Submission


def prepare_data_for_registration(
    submission: Submission, context: dict, options: dict, object_mapping: dict
) -> dict:
    # Prepare the submission data for sending it to the Objects API. This requires
    # rendering the configured JSON template and running some basic checks for
    # security and validity, before throwing it over the fence to the Objects API.

    record_data = render_to_json(options["content_json"], context)

    object_data = {
        "type": options["objecttype"],
        "record": {
            "typeVersion": options["objecttype_version"],
            "data": record_data,
            "startAt": get_today(),
        },
    }
    apply_data_mapping(submission, object_mapping, REGISTRATION_ATTRIBUTE, object_data)

    return object_data
