from typing import Any

from openforms.utils.date import get_today


def prepare_data_for_registration(
    record_data: dict[str, Any],
    objecttype: str,
    objecttype_version: int,
    geometry_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare the submission data for sending it to the Objects API."""

    data = {
        "type": objecttype,
        "record": {
            "typeVersion": objecttype_version,
            "data": record_data,
            "startAt": get_today(),
        },
    }
    if geometry_data is not None:
        data["record"]["geometry"] = geometry_data

    return data
