from datetime import date, datetime

from openforms.contrib.zgw.clients.catalogi import EigenschapSpecificatie
from openforms.typing import JSONValue, VariableValue


def process_according_to_eigenschap_format(
    specificatie: EigenschapSpecificatie, value: VariableValue
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
        case "tekst" | "getal", str() | float() | int():
            return value

        case "datum", date():
            return value.strftime("%Y%m%d")

        case "datum_tijd", datetime():
            assert value.tzinfo, "We expect timezone information to have been set"
            return value.strftime("%Y%m%d%H%M%S")

        case _:
            raise ValueError("Received value in unknown/unexpected format!")
