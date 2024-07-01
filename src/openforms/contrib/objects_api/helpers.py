from typing import Any

from openforms.utils.date import get_today


def prepare_data_for_registration(
    data: dict[str, Any],
    objecttype_version: int,
) -> dict[str, Any]:
    """Prepare the submission data for sending it to the Objects API."""

    return {
        "typeVersion": objecttype_version,
        "data": data,
        "startAt": get_today(),
    }
