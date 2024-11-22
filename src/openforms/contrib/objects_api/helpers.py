from openforms.typing import JSONObject
from openforms.utils.date import get_today

from .typing import Record


def prepare_data_for_registration(
    data: JSONObject,
    objecttype_version: int,
) -> Record:
    """Prepare the submission data for sending it to the Objects API."""

    return {
        "typeVersion": objecttype_version,
        "data": data,
        "startAt": get_today(),
    }
