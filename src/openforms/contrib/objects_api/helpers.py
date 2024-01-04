from typing import TypedDict

from openforms.contrib.zgw.clients.utils import (  # TODO: should be moved somewhere more generic?
    get_today,
)
from openforms.registrations.constants import REGISTRATION_ATTRIBUTE
from openforms.submissions.mapping import MappingConfig, apply_data_mapping
from openforms.submissions.models import Submission

from .rendering import render_to_json


class PrepareOptions(TypedDict):
    content_json: str  # Django template syntax
    objecttype: str  # URL to the objecttype in the Objecttypes API
    objecttype_version: int


def prepare_data_for_registration(
    submission: Submission,
    context: dict,
    options: PrepareOptions,
    object_mapping: MappingConfig,
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
