from datetime import date, datetime

import pytz


def process_according_to_eigenschap_format(specificatie: dict, value: str):
    """
    This is an extra validation we are doing against the eigenschap.specificatie.formaat
    since the value we send should be YYYYMMDD for date or YYYYMMDDHHmmSS for date/time.
    """
    format = specificatie.get("formaat")
    if format not in ["datum", "datum_tijd"]:
        return value

    if format == "datum":
        try:
            valid_date = date.fromisoformat(value)
        except ValueError as exc:
            raise exc

        processed_value = valid_date.strftime("%Y%m%d")

    elif format == "datum_tijd":
        try:
            valid_datetime = datetime.fromisoformat(value)
        except ValueError as exc:
            raise exc

        amsterdam_timezone = pytz.timezone("Europe/Amsterdam")
        localized_datetime = valid_datetime.replace(tzinfo=pytz.UTC).astimezone(
            amsterdam_timezone
        )

        processed_value = localized_datetime.strftime("%Y%m%d%H%M%S")

    return processed_value
