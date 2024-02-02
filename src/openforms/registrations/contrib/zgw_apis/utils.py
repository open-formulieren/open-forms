from datetime import date, datetime

from openforms.contrib.zgw.clients.utils import datetime_in_amsterdam


def process_according_to_eigenschap_format(specificatie: dict, value: str):
    """
    This is an extra validation we are doing against the eigenschap.specificatie.formaat
    since the value we send should be YYYYMMDD for date or YYYYMMDDHHmmSS for date/time.
    """
    format = specificatie.get("formaat")
    if format not in ["datum", "datum_tijd"]:
        return value

    if format == "datum":
        valid_date = date.fromisoformat(value)
        processed_value = valid_date.strftime("%Y%m%d")
    elif format == "datum_tijd":
        valid_datetime = datetime.fromisoformat(value)
        localized_datetime = datetime_in_amsterdam(valid_datetime)
        processed_value = localized_datetime.strftime("%Y%m%d%H%M%S")

    return processed_value
