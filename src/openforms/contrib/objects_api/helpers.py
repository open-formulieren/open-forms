from typing import Any

from openforms.utils.date import get_today


def prepare_data_for_registration(
    record_data: dict[str, Any],
    objecttype: str,
    objecttype_version: int,
) -> dict[str, Any]:
    """Prepare the submission data for sending it to the Objects API."""

    return {
        "type": objecttype,
        "record": {
            "typeVersion": objecttype_version,
            "data": record_data,
            "startAt": get_today(),
        },
    }
