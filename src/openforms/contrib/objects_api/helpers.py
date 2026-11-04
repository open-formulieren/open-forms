from of_datetime_utils import get_today
from openforms.typing import JSONObject

from .typing import Record


def prepare_data_for_registration(
    data: JSONObject,
    objecttype_version: int,
) -> Record:
    """Prepare the submission data for sending it to the Objects API."""

    return {
        "typeVersion": objecttype_version,
        "data": data,
        "startAt": get_today().isoformat(),
    }
