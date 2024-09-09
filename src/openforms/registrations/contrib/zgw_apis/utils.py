from datetime import date, datetime

from openforms.contrib.zgw.clients.catalogi import EigenschapSpecificatie
from openforms.typing import JSONValue
from openforms.utils.date import datetime_in_amsterdam


def process_according_to_eigenschap_format(
    specificatie: EigenschapSpecificatie, value: JSONValue
) -> JSONValue:
    """
    Process date/datetime values into the correct format for eigenschap.

    The zaken/catalogi API does not follow ISO-8601 for these, see github issue:
    https://github.com/VNG-Realisatie/gemma-zaken/issues/1751

    * date must be formatted as YYMMDD
    * datetime must localized in the NL (Amsterdam) timezone, and then formatted as
      YYYYMMDDHHmmSS

    Any other values we pass along as-is.
    """
    match specificatie["formaat"], value:
        # pass-through
        case "tekst" | "getal", _:
            return value

        case "datum", str():
            valid_date = date.fromisoformat(value)
            return valid_date.strftime("%Y%m%d")

        case "datum_tijd", str():
            valid_datetime = datetime.fromisoformat(value)
            localized_datetime = datetime_in_amsterdam(valid_datetime)
            return localized_datetime.strftime("%Y%m%d%H%M%S")

        case _:  # pragma: no cover
            raise ValueError("Received value in unknown/unexpected format!")
